import logging
from openerp import api, fields, models, _
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class SettlementSummaryGenerator(models.TransientModel):
    _name = 'settlement.summary.wizard'
    _description = 'Settlement Summary Report Generator'

    # def get_settlement_states(self):
    #     # TODO: Check
    #     return self.env['sale.commission.settlement']._fields['state'].selection

    date_from = fields.Date("Start Date", default=fields.Date.today(), required=True)
    date_to = fields.Date("End Date", default=fields.Date.today(), required=True)
    settlement_ids = fields.Many2many('sale.commission.settlement', string='Settlements')
    # state = fields.Selection(selection='get_settlement_states', string='Settlement State')

    def action_print_reports(self, cr, uid, ids, context=None):
        record = self.browse(cr,uid,ids[0],context=context)
        record._onchange_date_from()
        record._onchange_date_to()
        settlements = self.pool['sale.commission.settlement'].search(cr, uid,
        [
            ('date_from', '>=', record.date_from), 
            ('date_to', '<=', record.date_to), 
            ('state', '=', 'settled')
        ])
        record.settlement_ids = [(6, 0, settlements)]
        
        report_action = self.pool['report'].get_action(cr, uid, record.id, 'commissions_autolamps.report_settlement_summary', data=None, context=context)
        del report_action['report_type']
        return report_action

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            self.date_from = fields.Date.from_string(self.date_from) - relativedelta(day=1)

    @api.onchange('date_to')
    def _onchange_date_to(self):
        if self.date_to:
            self.date_to = fields.Date.from_string(self.date_to) - relativedelta(day=31)

    def get_total_payable(self):
        return sum(line.total_payable for line in self.settlement_ids)