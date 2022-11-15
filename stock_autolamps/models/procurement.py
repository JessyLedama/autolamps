from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp import tools
import logging
_logger = logging.getLogger(__name__)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_group = fields.Boolean(string='Sale Order Group', compute='_compute_sale_order_group', 
                                        store=True, default=False)
    
    @api.depends('name')
    def _compute_sale_order_group(self):
        for record in self:
            name = record.name
            if 'SO' in record.name and '/' in record.name:
                name = record.name.split('/')[0]
            sale_order = record.env['sale.order'].search([('name', '=', name)])
            record.sale_order_group = True if sale_order else False

    @api.constrains('sale_order_id', 'sale_order_group')
    def _constrains_sale_order_id_sale_order_group(self):
        for record in self:
            if record.sale_order_group and not record.sale_order_id:
                name = record.name
                if 'SO' in record.name and '/' in record.name:
                    name = record.name.split('/')[0]
                sale_id = record.env['sale.order'].search([('name', '=', name)], limit=1).id
                record.write({
                    'sale_order_id': sale_id
                })


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def remove_cancelled_procurement_orders(self, limit=1000, days=False):
        domain = [('state', '=', 'cancel')]
        if days:
            dt = datetime.now() + relativedelta(days=-days)
            domain += [('date_planned', '>=', fields.Datetime.to_string(dt))]
        procurements = self.env['procurement.order'].search(domain, limit=limit)
        procurements.unlink()
