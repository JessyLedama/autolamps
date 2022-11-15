# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions
from openerp import tools
from openerp.addons.stock.stock import stock_move as OriginalStockMove
import logging

_logger = logging.getLogger(__name__)


@api.cr_uid_ids_context
def _picking_assign(self, cr, uid, move_ids, procurement_group, location_from,
                    location_to, context=None):
    """Assign a picking on the given move_ids, which is a list of move supposed to share the same procurement_group, location_from and location_to
    (and company). Those attributes are also given as parameters.
    """
    pick_obj = self.pool.get("stock.picking")
    # Use a SQL query as doing with the ORM will split it in different queries with id IN (,,)
    # In the next version, the locations on the picking should be stored again.
    procurement_group_obj = self.pool.get("procurement.group").browse(cr, uid,
                                                                      procurement_group,
                                                                      context=context)
    query = ""
    if procurement_group_obj.sale_order_group:
        query = """
            SELECT stock_picking.id FROM stock_picking, stock_move
            WHERE
                stock_picking.state in ('draft', 'confirmed', 'waiting', 'partially_available', 'assigned') AND
                stock_move.picking_id = stock_picking.id AND
                stock_move.location_id = %s AND
                stock_move.location_dest_id = %s AND
        """
    else:
        query = """
            SELECT stock_picking.id FROM stock_picking, stock_move
            WHERE
                stock_picking.state in ('draft', 'confirmed', 'waiting') AND
                stock_move.picking_id = stock_picking.id AND
                stock_move.location_id = %s AND
                stock_move.location_dest_id = %s AND
        """
    params = (location_from, location_to)
    if not procurement_group:
        query += "stock_picking.group_id IS NULL LIMIT 1"
    else:
        query += "stock_picking.group_id = %s LIMIT 1"
        params += (procurement_group,)
    cr.execute(query, params)
    [pick] = cr.fetchone() or [None]
    sale_obj = self.pool.get('sale.order')
    domain = [('procurement_group_id', '=', procurement_group)]
    sales = sale_obj.search(cr, uid, domain, context=context)

    if not pick:
        move = self.browse(cr, uid, move_ids, context=context)[0]
        values = self._prepare_picking_assign(cr, uid, move, context=context)
        pick = pick_obj.create(cr, uid, values, context=context)
    res = self.write(cr, uid, move_ids, {'picking_id': pick}, context=context)
    # TODO: Figure out if this also works if the the group is weirdly named?
    if (sales and len(sales) == 1) or procurement_group_obj.sale_order_group:
        pickings = self.browse(cr, uid, move_ids, context=context).mapped(
            'picking_id')
        self.pool.get('stock.picking').browse(cr, uid, pickings.ids,
                                              context=context).action_assign()
    return res


OriginalStockMove._picking_assign = _picking_assign


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'name desc'

    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order', related='group_id.sale_order_id')
    sale_order_group = fields.Boolean(
        string='Sale Order Group', related='group_id.sale_order_group',
        default=False, store=True)
    original_picking_ids = fields.Many2many('stock.picking',
        'stock_picking_originator_rel', 'original_picking_id', 'pick_id', string='Origin Pickings', 
        compute='_compute_original_picking_ids', store=True)

    # For SMS
    delivery_sms_sent = fields.Boolean("SMS Sent")
    delivery_carrier_id = fields.Many2one('delivery.courier', "Courier")
    waybill = fields.Char("WayBill")
    template_id = fields.Many2one('sms.template', "SMS Template")
    sms_body = fields.Text("SMS Body")

    @api.onchange('delivery_carrier_id', 'waybill', 'template_id')
    def _onchange_dispatch_details(self):
        if not self.partner_id:
            raise exceptions.Warning("You need to fill the dispatch customer!")
        if not self.template_id:
            return
        sms_template = self.template_id.sms_html
        vals = {
            'name': self.partner_id.name,
            'reference': self.origin or "",
            'courier': self.delivery_carrier_id.name or "",
            'waybill': self.waybill or ""
        }

        content = sms_template % vals
        self.sms_body = content

    @api.multi
    def send_dispatch_sms(self):
        self.ensure_one()
        if not self.template_id:
            raise exceptions.Warning("Please select the template the use!")
        gateway = self.env['gateway.setup'].search([], limit=1)
        phone = self.partner_id.phone or self.partner_id.mobile
        sms = self.sms_body
        if phone and gateway:
            gateway._send_sms(self.partner_id, phone, sms)
            self.delivery_sms_sent = True
            # Post In Logs
            self.message_post(body=sms, subject="Dispatch SMS")
    
    @api.depends('move_lines', 'state')
    def _compute_original_picking_ids(self):
        for record in self:
            pickings = record.move_lines.mapped('move_orig_ids.picking_id.id')
            record.original_picking_ids = [(6, 0, pickings)]

    @api.multi
    def write(self, vals):
        if vals.get('workflow_process_id', False):
            sale_obj = self.env['sale.order']
            domain = [('procurement_group_id', '=', self.group_id.id)]
            sales = sale_obj.search(domain)
            if sales and len(sales) == 1:
                sale = sales[0]
                if not self.picking_type_id == sale.warehouse_id.out_type_id:
                    vals['workflow_process_id'] = False
        return super(StockPicking, self).write(vals)


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    variance = fields.Integer(string="Variance", compute='_stock_difference')

    # calculate variance
    @api.one
    @api.depends('theoretical_qty', 'product_qty')
    def _stock_difference(self):
        self.variance = self.product_qty - self.theoretical_qty

    # trigger report
    @api.multi
    def print_stock_variance_report(self):
        return self.env['report'].get_action(
            self, 'stock_autolamps.report_stock_variance')


class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_done(self, cr, uid, ids, context=None):
        res = super(StockMove, self).action_done(cr, uid, ids, context=None)
        done_moves = [move for move in
                      self.browse(cr, uid, ids, context=context) if
                      move.state == "done"]
        done_pickings = [move.picking_id for move in done_moves if
                         move.picking_id.state == 'done']
        sale_obj = self.pool.get('sale.order')
        if done_pickings:
            for picking in done_pickings:
                if picking.state != 'done':
                    continue
                else:
                    domain = [
                        ('procurement_group_id', '=', picking.group_id.id)]
                    sales = sale_obj.search(cr, uid, domain, context=context)
                    if sales and len(sales) == 1:
                        other_pickings = self.pool.get('stock.picking').search(
                            cr, uid, [('group_id', '=', picking.group_id.id), (
                            'state', 'not in', ['draft', 'cancel', 'done'])],
                            context=context)
                        if other_pickings:
                            self.pool.get('stock.picking').browse(cr, uid,
                                                                  other_pickings,
                                                                  context=context).action_assign()
        return res


class StockHistory(models.Model):
    _inherit = 'stock.history'

    picking_id = fields.Many2one('stock.picking', string='Reference')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_history')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_history AS (
              SELECT MIN(id) as id,
                move_id,
                picking_id,
                location_id,
                company_id,
                product_id,
                product_categ_id,
                SUM(quantity) as quantity,
                date,
                COALESCE(SUM(price_unit_on_quant * quantity) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant,
                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    stock_move.picking_id AS picking_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                   stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                  AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    stock_move.picking_id AS picking_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                 AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, picking_id, location_id, company_id, product_id, product_categ_id, date, source
            )""")


class StockWarehouseOrderPoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    code = fields.Char("Code", compute='_compute_code', store=True)

    @api.multi
    @api.depends('product_id', 'product_id.product_sequence', 'location_id')
    def _compute_code(self):
        for this in self:
            code = "%s/%s" % (
            this.product_id.product_sequence, this.location_id.location_id.name)
            this.code = code


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    resupply_procurement_group_id = fields.Many2one('procurement.group',
                                                    string='Resupply Procurement Group')
