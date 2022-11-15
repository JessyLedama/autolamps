from openerp import api, fields, models, _


class AgentCommissionReportGenerator(models.TransientModel):
    _name = 'agent.commission.report.wizard'
    _description = 'Agent Commission Report Generator'

    date_from = fields.Date("Start Date", default=fields.Date.today())
    date_to = fields.Date("End Date", default=fields.Date.today())
    agent_ids = fields.Many2many('res.partner', string='Partners', required=True, domain="[('agent', '=', True)]")
    report_ids = fields.One2many('agent.commission.report', 'generator_id', string='Agent Reports')


    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(AgentCommissionReportGenerator, self).default_get(cr, uid, fields, context=context)
        agent_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not agent_ids:
            return res
        assert active_model in ('res.partner'), 'Bad context propagation'
        res.update(agent_ids=agent_ids)
        return res

    def action_print_reports(self, cr, uid, ids, context=None):
        report_ids_list = []
        record = self.browse(cr,uid,ids[0],context=context)
        for agent in record.agent_ids:
            vals = {
                'date_from': record.date_from,
                'date_to': record.date_to,
                'agent_id': agent.id,
                'generator_id': record.id
            }
            invoices = agent.get_invoices_by_date(record.date_from, record.date_to)
            vals['report_line_ids'] = []
            if invoices:
                for invoice in invoices:
                    vals['report_line_ids'] += [(0, 0, {'invoice_id': invoice.id})]
                report = self.pool['agent.commission.report'].create(cr, uid, vals)
                report_ids_list.append(report)
        report_action = self.pool['report'].get_action(cr, uid, report_ids_list, 'commissions_autolamps.report_agent_commission', data=None, context=context)
        del report_action['report_type']
        return report_action
        # {'type': 'ir.actions.report.xml', 'report_name':'xml_id_of_report'}
        #  {'type': 'ir.actions.act_window_close'}
        

class AgentCommissionReport(models.TransientModel):
    _name = 'agent.commission.report'
    _description = 'Agent Commission Report'

    generator_id = fields.Many2one('agent.commission.report.wizard', string='Agent Report Generator', required=True)
    agent_id = fields.Many2one('res.partner', string='Agent')
    report_line_ids = fields.One2many('agent.commission.report.line', 'report_id', string='Agent Invoice Report Lines')
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    total = fields.Float(compute='_compute_total', string='Total')

    @api.depends('report_line_ids', 'report_line_ids.total_invoice_commission')
    def _compute_total(self):
        for record in self:
            record.total = sum(line.total_invoice_commission for line in record.report_line_ids)

    def get_total_commission(self):
        return sum(line.total_invoice_commission for line in self.report_line_ids)

    def get_total(self):
        return sum(line.invoice_total for line in self.report_line_ids)

    def get_net_sales(self):
        return self.get_total() - self.agent_id.target

    def get_payable_factor(self):
        if self.agent_id.target > 0:
            payable_factor = (self.get_net_sales() / self.agent_id.target)
            payable_factor = 1 if payable_factor > 1 else payable_factor
            payable_factor = 0 if payable_factor < 0 else payable_factor
        else:
            payable_factor = 1
        return payable_factor
            
    def get_payable_commission(self):
        return self.get_payable_factor() * self.get_total_commission()

class AgentCommissionReportLines(models.TransientModel):
    _name = 'agent.commission.report.line'
    _description = 'Agent Commission Report Lines'

    report_id = fields.Many2one('agent.commission.report', string='Agent Commission Report', required=True)
    agent_id = fields.Many2one('res.partner', string='Agent', related='report_id.agent_id')
    invoice_id = fields.Many2one('account.invoice', string='Commission Invoice', required=True)
    invoice_date = fields.Date(string="Invoice Date", related="invoice_id.date_invoice")
    invoice_total = fields.Float(string="Invoice Total", compute='_compute_total_invoice_commission')
    sale_orders = fields.Char(string='Sale Orders', compute='_compute_sale_orders')
    # settlement_id = fields.Many2one('sale.commission.settlement', string='Settlement', compute='_compute_settlement_id')
    # TODO: Get generated invoice for this settlement
    # settlement_invoice_id = fields.Many2one('account.invoice', string='Settlement Invoice', related='settlement_id.invoice')
    total_invoice_commission = fields.Float(compute='_compute_total_invoice_commission', string='Total Invoice Commission')

    @api.depends('invoice_id', 'agent_id')
    def _compute_sale_orders(self):
        for record in self:
            sale_orders = record.agent_id.get_invoice_sale_orders(record.invoice_id)
            record.sale_orders = ','.join(sale_orders.mapped('name'))

    @api.depends('invoice_id', 'agent_id')
    def _compute_total_invoice_commission(self):
        for record in self:
            agent_lines = record.agent_id.invoice_agent_line_ids.filtered(lambda line: line.invoice.id == record.invoice_id.id)
            record.total_invoice_commission = sum(line.amount for line in agent_lines)
            record.invoice_total = sum(line.total_amount for line in agent_lines)

    # @api.depends('invoice_id', 'agent_id')
    # def _compute_settlement_id(self):
    #     for record in self:
    #         s = record.agent_id.settlement_ids.filtered(lambda s: record.invoice_id.id in s.lines.invoice.ids)
    #         # TODO: Test this; Is s one?
    #         record.settlement_id = s
