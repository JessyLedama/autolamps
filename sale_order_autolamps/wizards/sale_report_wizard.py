import logging
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, exceptions

_logger = logging.getLogger(__name__)


class SaleReportGenerator(models.TransientModel):
    _name = 'sale.report.wizard'
    _description = 'Sale Report Generator'

    # sale_order_ids = fields.Many2many('sale.order', string='Sale Orders')
    # total = fields.Float(compute='_compute_total', string='Total')

    # @api.depends('sale_order_ids', 'sale_order_ids.amount_total')
    # def _compute_total(self):
    #     for record in self:
    #         record.total = sum(line.amount_total for line in record.sale_order_ids)

    # def default_get(self, cr, uid, fields, context=None):
    #     if context is None: context = {}
    #     res = super(SaleReportGenerator, self).default_get(cr, uid, fields, context=context)
    #     sale_order_ids = context.get('active_ids', [])
    #     active_model = context.get('active_model')

    #     if not sale_order_ids:
    #         return res
    #     assert active_model in ('sale.order'), 'Bad context propagation'
    #     res.update(sale_order_ids=sale_order_ids)
    #     return res

    def action_print_reports(self, cr, uid, ids, context=None):
        # self.default_get(cr, uid, fields, context=None)
        # TODO: Get sale order ids from context
        # report_ids_list = []
        # record = self.browse(cr,uid,ids[0],context=context)
        # _logger.info("logging stuff")
        # _logger.info(records)
        # _logger.info(ids)
        # _logger.info(data)
        # report_action = self.pool['report'].get_action(cr, uid, record.id, 'sale_order_autolamps.report_sale_order_summary', data=None, context=context)
        # del report_action['report_type']
        # return report_action 
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'sale.order',
            'form': data
        }

        datas['form']['active_ids'] = context.get('active_ids', False)

        return self.pool['report'].get_action(cr, uid, [], 'sale_order_autolamps.report_sale_order_summary', data=datas, context=context)
        # return exceptions.ValidationError("No orders to print")

    def print_sale_orders(self, cr, uid, ids, context=None):
        ids_list = []
        records = self.browse(cr,uid,ids,context=context)
        if records:
            # data['form'].update(self.read(cr, uid, ids, ['name', 'date_order', ''], context=context)[0])
            data = {}
            data['form'] = records
            _logger.info("logging stuff")
            _logger.info(records)
            _logger.info(ids)
            _logger.info(data)
            report_action = self.pool['report'].get_action(cr, uid, self.id, 'sale_order_autolamps.report_sale_order_summary', data=data, context=context)
            del report_action['report_type']
            return report_action 
        return exceptions.ValidationError("No orders to print")
        

# class SaleReport(models.TransientModel):
#     _name = 'sale.report'
#     _description = 'Sale Report'

#     generator_id = fields.Many2one('sale.report.wizard', string='Sale Report Generator', required=True)
#     report_line_ids = fields.One2many('sale.report.line', 'report_id', string='Sale Order Report Lines')
#     total = fields.Float(compute='_compute_total', string='Total')

#     @api.depends('report_line_ids', 'report_line_ids.order_total')
#     def _compute_total(self):
#         for record in self:
#             record.total = sum(line.order_total for line in record.report_line_ids)


# class SaleReportLines(models.TransientModel):
#     _name = 'sale.report.line'
#     _description = 'Sale Report Lines'

#     report_id = fields.Many2one('sale.report', string='Sale Report', required=True)
#     order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
#     order_date = fields.Date(string="Order Date", related="order_id.date_invoice")
#     order_total = fields.Float(string="Order Total", related="order_id.date_invoice")
#     # TODO: PARTNER NAME, SALESPERSON, STATE

#     @api.depends('invoice_id', 'agent_id')
#     def _compute_sale_orders(self):
#         for record in self:
#             sale_orders = record.agent_id.get_invoice_sale_orders(record.invoice_id)
#             record.sale_orders = ','.join(sale_orders.mapped('name'))

#     @api.depends('invoice_id', 'agent_id')
#     def _compute_total_invoice_commission(self):
#         for record in self:
#             agent_lines = record.agent_id.invoice_agent_line_ids.filtered(lambda line: line.invoice.id == record.invoice_id.id)
#             record.total_invoice_commission = sum(line.amount for line in agent_lines)
#             record.invoice_total = sum(line.total_amount for line in agent_lines)

    # @api.depends('invoice_id', 'agent_id')
    # def _compute_settlement_id(self):
    #     for record in self:
    #         s = record.agent_id.settlement_ids.filtered(lambda s: record.invoice_id.id in s.lines.invoice.ids)
    #         # TODO: Test this; Is s one?
    #         record.settlement_id = s
