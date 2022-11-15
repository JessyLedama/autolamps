# -*- coding: utf-8 -*-
import logging
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, exceptions

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_default_workflow(self):
        workflow = self.env['ir.values'].sudo().get_default(
            'sale.config.settings', 'default_workflow_id')
        return workflow

    agent_id = fields.Many2one(
        'res.partner', string="Agent", domain="[('agent', '=', True')]")
    pricelist_editable = fields.Boolean(
        compute='_compute_pricelist_editable', string='Pricelist Editable',
        store=True)
    workflow_process_id = fields.Many2one(
        'sale.workflow.process', ondelete='restrict',
        default=_get_default_workflow)
    sourced_order_line = fields.One2many('sale.order.line.sourced', 'order_id', string='Sourced Order Lines', readonly=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        'Default Warehouse',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="If no source warehouse is selected on line, this warehouse is used as default. ")

    @api.model
    def create(self, vals):
        _logger.info("order create values %s" % vals)
        res = super(SaleOrder, self).create(vals)
        if res.state == 'draft' and res.client_order_ref:
            res.client_order_ref = False
        if 'agent_id' in vals:
            res._update_commission()
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'agent_id' in vals:
            self._update_commission()
        return res

    @api.multi
    def _update_commission(self):
        self.ensure_one()
        for order in self.order_line:
            # order.agents = False
            agents = order.product_id.agents
            if agents:
                order._update_commission()
    
    @api.depends('user_id', 'user_id.groups_id')
    def _compute_pricelist_editable(self):
        for order in self:
            order.pricelist_editable = order.user_has_groups('autolamps_base.group_edit_sale_pricelist')

    def _prepare_procurement_group(self, cr, uid, order, context=None):
        return {'name': order.name, 'partner_id': order.partner_shipping_id.id, 'sale_order_id': order.id}

    def action_check_availability(self, cr, uid, ids, context=None):
        record = self.browse(cr,uid,ids[0],context=context)
        warehouse_has_priority = record.warehouse_id.check_warehouse_priority()
        if record.order_line and warehouse_has_priority:
            if record.sourced_order_line:
                record.sourced_order_line.unlink()
            record.check_duplicates()
            for order_line in record.order_line:
                record.pool.get('sale.order.line.sourced').check_product_availabilty(order_line)
                # Call to update quantity on order line
                record.update_ordered_quantity(order_line)
            record.clean_lines()
        else:
            raise exceptions.ValidationError("""No warehouse priority is set on this warehouse. 
            Configure one or use another warehouse.""")

    def update_ordered_quantity(self, order_line):
        _logger.info('self in update ordered qty %s' % self)
        _logger.info('order_line.order_id %s' % order_line.order_id)
        available_quantity = sum(order_line.order_id.sourced_order_line.filtered(lambda l: l.product_id == order_line.product_id).mapped('product_uom_qty'))
        order_line.with_context(source_items=True).write({
            'product_uom_qty': available_quantity
        })

    def clean_lines(self):
        # NEW: Fix order_line
        for line in self.sourced_order_line:
            if line.product_uom_qty == 0:
                line.unlink()

    def check_duplicates(self):
        products = set()
        for line in self.order_line:
            if line.product_id in products:
                raise exceptions.Warning("""The product %s appears twice in the order lines.
             Please fix this and try again.""" % line.product_id.name)
            else:
                products.add(line.product_id)

    def get_procurement_values(self, line):
        route = False 
        sale_line_id = False
        product_uos_qty = False
        product_uos = False
        location_id = False
        route_id = False

        if not line.order_id.procurement_group_id:
            vals = self._prepare_procurement_group(line.order_id)
            group_id = self.env["procurement.group"].create(vals)
            line.order_id.write({'procurement_group_id': group_id.id})

        if hasattr(line, 'sale_order_line_id'):
            date_planned = self._get_date_planned(line.order_id, line.sale_order_line_id, line.order_id.date_order)
            route = line.order_id.warehouse_id.get_priority_warehouse_route(line.warehouse_id)
            sale_line_id = line.sale_order_line_id.id
            product_uos_qty = line.product_uom_qty
            product_uos = line.product_uom.id
            location_id = line.order_id.warehouse_id.lot_stock_id.id 
            route_id = route and [(4, route.id)] or []
            invoice_state = 'none'
        else:
            date_planned = self._get_date_planned(line.order_id, line, line.order_id.date_order)
            product_uos_qty = (line.product_uos and line.product_uos_qty) or line.product_uom_qty
            product_uos = (line.product_uos and line.product_uos.id) or line.product_uom.id
            sale_line_id = line.id
            location_id = line.order_id.partner_shipping_id.property_stock_customer.id
            route_id = line.route_id and [(4, line.route_id.id)] or []
            invoice_state = (line.order_id.order_policy == 'picking') and '2binvoiced' or 'none'
            
            if not line.procurement_group_id:
                line.write({
                    'procurement_group_id': line.order_id.procurement_group_id.id
                })

        # TODO: See if below line is necessary
        # vals['partner_dest_id'] = order.partner_shipping_id.id
        if line.product_uom_qty <= 0:
            return {}
        values = {
            'name': line.name,
            'origin': line.order_id.name,
            'date_planned': date_planned,
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': product_uos_qty,
            'product_uos': product_uos,
            'company_id': line.order_id.company_id.id,
            'group_id': line.order_id.procurement_group_id.id,
            'invoice_state': invoice_state,
            'sale_line_id': sale_line_id,
            'warehouse_id': line.order_id.warehouse_id.id,
            'location_id': location_id,
            'route_ids': route_id
        }
        return values

    def _create_procurements(self, line, order_line=False):
        values = self.get_procurement_values(line)
        ctx = self._context.copy()
        ctx['procurement_autorun_defer'] = True
        if bool(values):
            self.env['procurement.order'].sudo().create(values, context=ctx)

    def create_procurements(self):
        for line in self.order_line:
            # Create procurement for whole line to customer
            if not line.product_uom_qty or not line.product_uos_qty:
                continue
            self._create_procurements(line)
            # Create procurements for replenishment from warehouses
            for s_line in self.sourced_order_line.filtered(lambda l: l.product_id.id == line.product_id.id and l.warehouse_id.id != line.order_id.warehouse_id.id):
                self._create_procurements(s_line)

    def get_checked_warehouses(self, line):
        return [line.warehouse_id.id for line in self.sourced_order_line.filtered(lambda l: l.product_id == line.product_id)]

    def all_warehouses_checked(self, line):
        checked_warehouses = self.get_checked_warehouses(line)
        _logger.info('checked warehouses %s' % checked_warehouses)
        all_warehouses = line.order_id.warehouse_id.get_priority_warehouse_ids()
        all_warehouses.append(line.order_id.warehouse_id.id)
        _logger.info('all warehouses %s' % all_warehouses)
        # _logger.info('all_warehouses_checked %s' % sorted(all_warehouses) == sorted(checked_warehouses))
        return sorted(all_warehouses) == sorted(checked_warehouses)

    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        res = super(SaleOrder, self)._prepare_order_line_procurement(cr, uid, order, line, group_id=False, context=None)
        qty = (line.product_uos and line.product_uos_qty) or line.product_uom_qty
        if qty <= 0:
            return {}
        return res

    def action_ship_create(self, cr, uid, ids, context=None):
        """Create the required procurements to supply sales order lines, also
        connecting the procurements to appropriate stock moves in order to
        bring the goods to the sales order's requested location.

        :return: True
        """
        _logger.info('action ship create')
        # Call to action check availability
        self.action_check_availability(cr, uid, ids, context=None)
        # Call to create procurements
        records = self.browse(cr, uid, ids, context=context)
        records.create_procurements()

        procurement_obj = self.pool.get('procurement.order')
        sale_line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=context):
            proc_ids = []

            groups = {}

            for line in order.order_line:
                if order.state == 'shipping_except':
                    groups[line._get_procurement_group_key()] = \
                        line.procurement_group_id.id

                group_id = groups.get(line._get_procurement_group_key())

                if not group_id:
                    vals = self._prepare_procurement_group_by_line(
                        cr, uid, line, context=context)
                    group_id = self.pool["procurement.group"].create(
                        cr, uid, vals, context=context)
                    groups[line._get_procurement_group_key()] = group_id
                if not line.procurement_group_id:
                    line.write({'procurement_group_id': group_id})
                # Try to fix exception procurement (possible when after a
                # shipping exception the user choose to recreate)
                if line.procurement_ids:
                    # first check them to see if they are in exception or not
                    # (one of the related moves is cancelled)
                    procurement_obj.check(
                        cr, uid, [x.id for x in line.procurement_ids
                                  if x.state not in ['cancel', 'done']])
                    line.refresh()
                    # run again procurement that are in exception in order to
                    # trigger another move
                    proc_ids += [x.id for x in line.procurement_ids
                                 if x.state in ('exception', 'cancel')]
                    procurement_obj.reset_to_confirmed(cr, uid, proc_ids,
                                                       context=context)
                elif sale_line_obj.need_procurement(cr, uid, [line.id],
                                                    context=context):
                    if (line.state == 'done') or not line.product_id:
                        continue
                    vals = self._prepare_order_line_procurement(
                        cr, uid, order, line,
                        group_id=group_id, context=context)
                    if bool(vals):
                        proc_id = procurement_obj.create(
                            cr, uid, vals, context=context)
                        proc_ids.append(proc_id)
            # Confirm procurement order such that rules will be applied on it
            # note that the workflow normally ensure proc_ids isn't an empty
            # list
            procurement_obj.run(cr, uid, proc_ids, context=context)

            # if shipping was in exception and the user choose to recreate the
            # delivery order, write the new status of SO
            if order.state == 'shipping_except':
                val = {'state': 'progress', 'shipped': False}

                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced and
                                line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
                order.write(val)
        return True

    def action_print_picking(self, cr, uid, ids, context=None):
        ids_list = []
        record = self.browse(cr,uid,ids[0],context=context)
        if record.picking_ids:
            for picking in record.picking_ids:
                ids_list.append(picking.id)
            return self.pool['report'].get_action(cr, uid, ids_list, 'stock.report_picking', data=None, context=context)
        return exceptions.ValidationError("No picking to print")

    def print_sale_orders(self, cr, uid, ids, context=None):
        records = self.browse(cr,uid,ids,context=context)
        if records:
            # data['form'].update(self.read(cr, uid, ids, ['name', 'date_order', ''], context=context)[0])
            data = {}
            data['form'] = records
            _logger.info(records)
            _logger.info(ids)
            _logger.info(data)
            return self.pool['report'].get_action(cr, uid, [], 'sale_order_autolamps.report_sale_order_summary', data=data, context=context)
        return exceptions.ValidationError("No orders to print")
               
    @api.multi
    def action_product_search(self):
        graph_view_ref = self.env.ref('pos_autolamps.pos_stock_quant_view_graph', False)
        tree_view_ref = self.env.ref('pos_autolamps.pos_view_stock_quant_tree', False)
        domain = []
        if len(self.order_line)>0:
            domain = [('product_id','in',[product_id.id for product_id in self.order_line.mapped('product_id')])]
        return { 
            'name': "Sale Product Search",
            'view_mode': 'graph, tree',
            'view_id': False,
            'view_type': 'graph',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'views': [(graph_view_ref and graph_view_ref.id or False, 'graph'),
                      (tree_view_ref and tree_view_ref.id or False, 'tree')],
            'context': {'search_default_internal_loc': 1, 'search_default_productgroup':1, 'search_default_locationgroup':1}
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'order_id desc, sequence, id, product_id'

    product_id = fields.Many2one('product.product', required=True)
    product_original_qty = fields.Float('Quantity Ordered', digits_compute=dp.get_precision('Product UoS'), required=True, readonly=True)
    product_original_uom = fields.Many2one('product.uom', 'Unit of Measure ', required=True, readonly=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        'Source Warehouse',
        help="If a source warehouse is selected, "
             "it will be used to define the route. "
             "Otherwise, it will get the warehouse of "
             "the sale order")
    lost_sale_qty = fields.Float(compute='_compute_lost_sale_qty', string='Sale Qty Lost', store=True, default=0.0)
    lost_sale_amount = fields.Float(compute='_compute_lost_sale_amount', string='Lost Sales Amount', store=True, default=0.0)
    date_order = fields.Datetime(string='Date Ordered', related='order_id.date_order', store=True)
    
    @api.depends('lost_sale_qty', 'order_id', 'order_id.partner_id', 'order_id.pricelist_id',
     'order_id.pricelist_id.currency_id', 'tax_id', 'product_id', 'price_unit', 'discount')
    def _compute_lost_sale_amount(self):
        for record in self:
            price = self._calc_line_base_price(record)
            taxes = record.tax_id.compute_all(price, record.lost_sale_qty,
                                        record.product_id,
                                        record.order_id.partner_id)
            record.lost_sale_amount = record.order_id.pricelist_id.currency_id.round(taxes['total'])

    @api.depends('product_original_qty', 'product_uom_qty', 'product_uos_qty')
    def _compute_lost_sale_qty(self):
        for record in self:
            sale_qty = record.product_uom_qty or record.product_uos_qty
            if record.product_original_qty == 0:
                record.lost_sale_qty = 0
            else:
                record.lost_sale_qty = abs(record.product_original_qty - sale_qty)

    @api.model
    def create(self, vals):
        _logger.info('order line vals %s' % vals)
        if vals.get('product_uom_qty', False) or vals.get('product_uos_qty', False):
            vals['product_original_qty'] = vals.get('product_uom_qty', False) or vals.get('product_uos_qty')
        _logger.info('order line vals %s' % vals)
        res = super(SaleOrderLine, self).create(vals)
        res._update_commission()
        _logger.info('result ordered qty %s' % res.product_original_qty)
        return res

    @api.multi
    def write(self, vals):
        if 'price_unit' in vals:
            if not self.user_has_groups('autolamps_base.group_edit_prices'):
                old_price = self.price_unit
                new_price = vals.get('price_unit', 0)
                if old_price > new_price:
                    raise exceptions.AccessError(
                        'You don\'t have Rights to change the Product Price for %s. '
                        'Contact Administrator!' % self.product_id.name)
        res = super(SaleOrderLine, self).write(vals)
        if 'product_id' in vals:
            self._update_commission()
        if 'product_uom_qty' in vals and self.state == 'draft':
            _logger.info('product_uom_qty is being written')
            _logger.info('state %s' % self.state)
            _logger.info('product_uom_qty %s' % self.product_uom_qty)
            _logger.info('product_original_qty %s' % self.product_original_qty)
            if 'source_items' not in self._context:
                _logger.info('source items in context')
                self.update_quantity_ordered()
        return res

    def update_quantity_ordered(self):
        if self.product_uom_qty != self.product_original_qty:
            self.write({
                'product_original_qty': self.product_uom_qty
            })

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # TODO: test above
        if self.product_uom_qty != self.product_original_qty and self.state == 'draft':
            self.write({
                'product_original_qty': self.product_uom_qty
            })

    @api.multi
    def _update_commission(self):
        self.ensure_one()
        if self.order_id.agent_id:
            # Proceed with updating the commission line
            agent_list = []
            # default commission_id for agent
            prod = self.product_id
            if prod.agents:
                self.agents.unlink()
                for this in prod.agents:
                    agent_list.append(
                        {
                            'agent': self.order_id.agent_id.id,
                            'commission': this.commission.id,
                        }
                    )
                self.write({
                    'agents': [(0, 0, x) for x in agent_list]
                })
        else:
            # Agent has been deleted, clear the lines
            self.agents.unlink()

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):

        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)
        agent_id = self.env.context.get('agent_id')
        if agent_id and product:
            agent_list = []
            # default commission_id for agent
            prod = self.env["product.product"].browse(product)
            if prod.agents:
                for this in prod.agents:
                    agent_list.append(
                        {
                            'agent': agent_id,
                            'commission': this.commission.id,
                       }
                    )

            res['value']['agents'] = [(0, 0, x) for x in agent_list]

        return res


class SaleOrderLineSourced(models.Model):
    _name = 'sale.order.line.sourced'
    _description = 'Sourced Line'
    # _order = 'order_id desc, sequence, id, product_id'

    name = fields.Char(string='Name')
    order_id = fields.Many2one('sale.order', 'Order Reference', required=True, ondelete='cascade', select=True, readonly=True)
    product_id = fields.Many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True, readonly=True, ondelete='restrict')
    product_uom_qty = fields.Float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True, readonly=True)
    product_original_qty = fields.Float('Quantity Ordered', digits_compute=dp.get_precision('Product UoS'), required=True, readonly=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure ', required=True, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse', help="If a source warehouse is selected, "
             "it will be used to define the route. "
             "Otherwise, it will get the warehouse of "
             "the sale order")
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order line')

    def all_warehouses_checked(self, line):
        return line.order_id.all_warehouses_checked(line)

    def get_product_available(self, product, warehouse):
        qty = product.with_context(warehouse=warehouse)._product_available()[product.id]['qty_available_not_res']
        qty = qty if qty > 0 else 0
        return qty

    def set_warehouse_qty(self, line, warehouse, new_line_qty):
        # remainder = line.product_uom_qty - new_line_qty
        remainder = line.product_original_qty - new_line_qty
        _logger.info('remainder %s' % remainder)
        line.write({
            'warehouse_id': warehouse,
            'product_uom_qty': new_line_qty,
        })
        if remainder and not self.all_warehouses_checked(line):
            self.refactor_line(line, remainder, warehouse)

    # TODO: Get warehouse qty func
    def get_warehouse_qty(self, line, warehouse):
        product_available = self.get_product_available(line.product_id, warehouse)
        _logger.info("product available: %s" % product_available)
        _logger.info('line.product_original_qty %s' % line.product_original_qty)
        _logger.info('line.product_uom_qty %s' % line.product_uom_qty)
        # new_line_qty = line.product_uom_qty if product_available >= line.product_uom_qty else product_available
        new_line_qty = line.product_original_qty if product_available >= line.product_original_qty else product_available
        _logger.info('new_line_qty %s' % new_line_qty)
        self.set_warehouse_qty(line, warehouse, new_line_qty)
        # return product_available >= line.product_uom_qty
        # return product_available >= line.product_original_qty

    def check_product_availabilty(self, line):
        warehouse = line.order_id.warehouse_id.id
        new_line = self.create_sourcing_line(line)
        # TODO: Rewrite this so that we call something that manages get_warehouse_qty, source_products
        self.get_warehouse_qty(new_line, warehouse)
    
    # NEW
    def create_sourcing_line(self, line):
        new_line_values = {
                "name": line.name,
                "product_uom_qty": line.product_uom_qty or line.product_uos_qty,
                "product_original_qty": line.product_original_qty,
                "product_uom": line.product_uom.id or line.product_uos.id,
                "order_id": line.order_id.id,
                "warehouse_id": line.warehouse_id.id,
                "product_id": line.product_id.id,
                "sale_order_line_id": line.id,
                }
        new_line = line.env['sale.order.line.sourced'].create(new_line_values)
        return new_line

    def create_spill_line(self, line, remainder):
        new_line = line.copy()
        new_line.write({
            'product_uom_qty': remainder,
            'product_original_qty': remainder,
        })
        return new_line

    def get_warehouse_priority_list(self, line, warehouse):
        warehouses_to_search = self._get_warehouse_priority_list(line.order_id.warehouse_id)
        if warehouse in warehouses_to_search:
            warehouses_to_search.remove(warehouse)
        return warehouses_to_search

    def _get_warehouse_priority_list(self, warehouse):
        return warehouse.get_priority_warehouse_ids()

    def check_warehouses(self, line, warehouse_list):
        checked_warehouses = line.order_id.get_checked_warehouses(line)
        return [warehouse for warehouse in warehouse_list if warehouse not in checked_warehouses]

    def next_warehouse(self, line):
        checked_warehouses = line.order_id.get_checked_warehouses(line)
        _logger.info('checked_warehouses %s' % checked_warehouses)
        all_warehouses = self._get_warehouse_priority_list(line.order_id.warehouse_id)
        _logger.info('all_warehouses %s' % all_warehouses)
        warehouses_left = [warehouse for warehouse in all_warehouses if warehouse not in checked_warehouses]
        _logger.info('warehouses_left %s' % warehouses_left)
        # TODO: Order warehouse accordig to priority
        # TODO: Make sure the warehouses_left is a list
        # _logger.info('warehouses_left[0] %s' % warehouses_left[0])
        if warehouses_left:
            return warehouses_left[0]
        return False

    def refactor_line(self, line, remainder, warehouse_id):
        warehouse_to_search = self.next_warehouse(line)
        if warehouse_to_search:
            new_line = self.create_spill_line(line, remainder)
            self.get_warehouse_qty(new_line, warehouse_to_search)