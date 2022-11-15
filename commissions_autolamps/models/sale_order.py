# -*- coding: utf-8 -*-

from openerp import models, fields, api

class SaleOrderLineAgent(models.Model):
    _inherit = "sale.order.line.agent"

    product_id = fields.Many2one(comodel_name='product.product', string='Product', related='sale_line.product_id')
    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', related='sale_line.order_id')
    total_amount = fields.Float(string='Total Amount', related='sale_line.price_subtotal')
    date_order = fields.Datetime(string='Order Date', related='sale_order_id.date_order')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_agent_line_ids = fields.One2many(comodel_name='sale.order.line.agent', related='order_line.sale_agent_line_ids', string='Sale Agent Lines')

    @api.multi
    def action_view_agent_lines(self):
        form_view_ref = self.env.ref('commissions_autolamps.sale_order_line_agent_view_form', False)
        tree_view_ref = self.env.ref('commissions_autolamps.sale_order_line_agent_view_tree', False)
        search_view_ref = self.env.ref('commissions_autolamps.sale_order_line_agent_view_search', False)
        domain = []
        if len(self.sale_agent_line_ids)>0:
            domain = [('sale_order_id','=',self.id)]
        return { 
            'name': "Agent Sale Commissions",
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'sale.order.line.agent',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'search_view_id': search_view_ref and search_view_ref.id or False,
            'views': [(tree_view_ref and tree_view_ref.id or False, 'tree'),
                (form_view_ref and form_view_ref.id or False, 'form'),
                      ],
        }

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sale_agent_line_ids = fields.One2many(comodel_name='sale.order.line.agent', inverse_name='sale_line', string='Sale Agent Lines')

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        vals = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            line, account_id=account_id)
        vals['agents'] = [
            (0, 0, {'agent': x.agent.id,
                    'commission': x.commission.id,
                    'sale_agent_line': x.id})
            for x in line.agents]
        return vals