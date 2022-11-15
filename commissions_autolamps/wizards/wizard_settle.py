
from openerp import models, fields, api, exceptions, _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class SaleCommissionMakeSettle(models.TransientModel):
    _inherit = "sale.commission.make.settle"

    @api.multi
    def action_settle(self):
        self.ensure_one()
        agent_line_obj = self.env['account.invoice.line.agent']
        settlement_obj = self.env['sale.commission.settlement']
        settlement_line_obj = self.env['sale.commission.settlement.line']
        settlement_invoice_obj = self.env['sale.commission.settlement.invoice']
        settlement_ids = []
        settlements = []
        if not self.agents:
            self.agents = self.env['res.partner'].search(
                [('agent', '=', True)])
        date_to = fields.Date.from_string(self.date_to)
        for agent in self.agents:
            date_to_agent = self._get_period_start(agent, date_to)
            # Get non settled invoices
            agent_lines = agent_line_obj.search(
                [('invoice_date', '<', date_to_agent),
                 ('agent', '=', agent.id),
                 ('settled', '=', False),
                 ('invoice.type', 'in', ('out_invoice', 'out_refund'))],
                order='invoice_date')
            for company in agent_lines.mapped('invoice_line.company_id'):
                agent_lines_company = agent_lines.filtered(
                    lambda r: r.invoice_line.company_id == company)
                if not agent_lines_company:
                    continue
                pos = 0
                sett_to = fields.Date.to_string(date(year=1900,
                                                     month=1,
                                                     day=1))
                while pos < len(agent_lines_company):
                    if (agent.commission.invoice_state == 'paid' and
                            agent_lines_company[pos].invoice.state !=
                            'paid'):
                        pos += 1
                        continue
                    if agent_lines_company[pos].invoice_date > sett_to:
                        sett_from = self._get_period_start(
                            agent, agent_lines_company[pos].invoice_date)
                        sett_to = fields.Date.to_string(
                            self._get_next_period_date(
                                agent, sett_from) - timedelta(days=1))
                        sett_from = fields.Date.to_string(sett_from)
                        settlement = settlement_obj.create(
                            {'agent': agent.id,
                             'date_from': sett_from,
                             'date_to': sett_to,
                             'company_id': company.id})
                        settlement_ids.append(settlement.id)
                        settlements.append(settlement)
                    settlement_line_obj.create(
                        {'settlement': settlement.id,
                         'agent_line': [(6, 0,
                                         [agent_lines_company[pos].id])
                                        ]})
                    pos += 1
        if len(settlements):
            for settlement in settlements:
                invoices = list(set(settlement.mapped('lines.invoice')))
                invoice_list = []
                for invoice in invoices:
                    if invoice not in invoice_list:
                        vals = {
                            'invoice_id': invoice.id,
                            'total_commission': invoice.get_commission_total_by_agent(agent),
                            'settlement_id': settlement.id
                        }
                        settlement_invoice_obj.create(vals)
                        invoice_list.append(invoice)

        # go to results
        if len(settlement_ids):
            return {
                'name': _('Created Settlements'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'sale.commission.settlement',
                'domain': [['id', 'in', settlement_ids]],
            }

        else:
            return {'type': 'ir.actions.act_window_close'}