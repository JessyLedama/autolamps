# -*- coding: utf-8 -*-
import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def default_date_paid(self):
        if self.state == 'paid' and self.payment_ids:
            dates = sorted(self.payment_ids.mapped('date'))
            return fields.Date.from_string(dates[-1])
        return False

    invoice_agent_line_ids = fields.One2many('account.invoice.line.agent', 'invoice', string='Invoice Agent Lines')
    date_paid = fields.Date(string='Payment Date',
        readonly=True, index=True, copy=False, default=False, compute='_compute_date_paid', store=True)

    @api.one
    @api.depends('reconciled')
    def _compute_date_paid(self):
        _logger.info("compute payment date")
        if self.reconciled:
            dates = sorted(self.payment_ids.mapped('date'))
            self.date_paid = fields.Date.from_string(dates[-1])
            _logger.info(self.date_paid)

    @api.multi
    def action_view_agent_lines(self):
        form_view_ref = self.env.ref('commissions_autolamps.account_invoice_line_agent_view_form', False)
        tree_view_ref = self.env.ref('commissions_autolamps.account_invoice_line_agent_view_tree', False)
        search_view_ref = self.env.ref('commissions_autolamps.account_invoice_line_agent_view_search', False)
        domain = []
        if len(self.invoice_agent_line_ids)>0:
            domain = [('invoice','=',self.id)]
        return { 
            'name': "Agent Sale Commissions",
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.invoice.line.agent',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'search_view_id': search_view_ref and search_view_ref.id or False,
            'views': [(tree_view_ref and tree_view_ref.id or False, 'tree'),
                    (form_view_ref and form_view_ref.id or False, 'form'),
                      ]}

    @api.constrains('date_paid')
    def _constrains_date_paid(self):
        _logger.info("constrain payment date")
        if self.reconciled and not self.date_paid:
            dates = sorted(self.payment_ids.mapped('date'))
            self.date_paid = fields.Date.from_string(dates[-1])

    @api.one
    @api.depends('invoice_line.agents.amount', 'invoice_line', 'invoice_line.agents')
    def _compute_commission_total(self):
        self.commission_total = 0.0
        for line in self.invoice_line:
            self.commission_total += sum(x.amount for x in line.agents)

    def get_commission_total_by_agent(self, agent):
        total_commission = 0
        for line in self.invoice_line:
            total_commission += sum(x.amount for x in line.agents.filtered(lambda a: a.agent.id == agent.id))
        return total_commission


class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    sale_agent_line = fields.Many2one('sale.order.line.agent', string='Sale Agent Line')
    total_amount = fields.Float(string='Total Amount', related='invoice_line.price_subtotal')