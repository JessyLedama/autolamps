import logging
from openerp import api, fields, models, exceptions, _

_logger = logging.getLogger(__name__)

class SaleSourcingReportGenerator(models.TransientModel):
    _name = 'sale.sourcing.report.wizard'
    _description = 'Sale Sourcing Report Generator'

    sale_order_ids = fields.Many2many('sale.order', string='Sale Orders', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses', required=True)

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(SaleSourcingReportGenerator, self).default_get(cr, uid, fields, context=context)
        sale_order_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not sale_order_ids:
            return res
        assert active_model in ('sale.order'), 'Bad context propagation'
        res.update(sale_order_ids=sale_order_ids)
        return res

    def action_print_reports(self, cr, uid, ids, context=None):
        report_ids = []
        record = self.browse(cr,uid,ids[0],context=context)
        for sale in record.sale_order_ids:
            vals = {
                'warehouse_ids': [(6, 0, record.warehouse_ids.ids)],
                'sale_order_id': sale.id,
                'generator_id': record.id
            }
            source_lines = []
            for source_line in sale.sourced_order_line:
                if source_line.warehouse_id in record.warehouse_ids:
                    source_lines.append(source_line.id)
            if source_lines:
                vals['report_line_ids'] = [(6, 0, source_lines)]
                report = self.pool['sale.sourcing.report'].create(cr, uid, vals)
                report_ids.append(report)
        if report_ids:
            report_action = self.pool['report'].get_action(cr, uid, report_ids, 'sale_order_autolamps.report_saleorder_sourcing', data=None, context=context)
            del report_action['report_type']
            return report_action
        raise exceptions.ValidationError(
                _('No lines to print!'))


class SaleSourcingReport(models.TransientModel):
    _name = 'sale.sourcing.report'
    _description = 'Sale Sourcing Report'

    generator_id = fields.Many2one('sale.sourcing.report.wizard', string='Sale Sourcing Report Generator', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses', required=True)
    report_line_ids = fields.Many2many('sale.order.line.sourced', string='Sourcing Lines')
    # total = fields.Float(compute='_compute_total', string='Total')
