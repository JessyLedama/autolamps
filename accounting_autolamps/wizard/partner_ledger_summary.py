# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import api, fields, models


class PartnerLedgerSummaryWizard(models.TransientModel):
    _name = 'partner.ledger.summary.wizard'
    _description = 'Partner Ledger Summary Wizard'

    @api.model
    def _get_default_from_date(self):
        dt = fields.Date.to_string(datetime.today().replace(month=1, day=1))
        return dt

    filter_date = fields.Boolean("Filter Date")
    partner_id = fields.Many2one('res.partner', "Partner")
    from_date = fields.Date('From', default=_get_default_from_date)
    to_date = fields.Date('To', default=datetime.today())

    account_type = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')],
        "Account Type's", required=True, default='customer_supplier')

    @api.multi
    def btn_generate_report(self):
        return self.env['report'].get_action(self, 'accounting_autolamps.report_ledger_summary')

    @api.multi
    def get_move_lines(self):
        from_date = False
        to_date = False
        if self.filter_date:
            from_date = self.from_date
            to_date = self.to_date
        if self.account_type == 'customer':
            account_types = ['receivable']
        elif self.account_type == 'supplier':
            account_types = ['payable']
        else:
            account_types = ['payable', 'receivable']
        move_lines = self.partner_id.get_ledger_summary(from_date, to_date, account_types)
        if self.filter_date:
            # Get balance up-to (from_date - 1 day)
            balance = self.partner_id.get_summary_initial_amounts(
                self.from_date, account_types)['balance'] or 0.0
            move_lines = [{
                'credit': 0.0,
                'amount': balance,
                'balance': balance,
                'debit': 0.00,
                'date': fields.Date.from_string(self.from_date).strftime('%d-%m-%Y'),
                'due': False,
                'transaction': "Balance Forward"
            }] + move_lines
        return move_lines

    @api.multi
    def get_from_to(self):
        from_dt = fields.Date.from_string(self.from_date).strftime('%d-%m-%Y')
        to_dt = fields.Date.from_string(self.to_date).strftime('%d-%m-%Y')

        return "%s - %s" % (from_dt, to_dt)

    @api.multi
    def get_amount_due(self):
        _1_dt = fields.Date.from_string(fields.Date.today())
        _30_dt = _1_dt + timedelta(days=-30)
        _60_dt = _30_dt + timedelta(days=-30)
        _90_dt = _60_dt + timedelta(days=-30)
        due_1_30 = self._get_due_per_duration(_30_dt, _1_dt)
        due_31_60 = self._get_due_per_duration(_60_dt, _30_dt)
        due_61_90 = self._get_due_per_duration(_90_dt, _60_dt)
        over_90 = self._get_due_per_duration(False, _90_dt)
        return {
            # 'current': self._get_due_per_duration(_1_dt, False),
            'current': self._get_balance_due(),
            '1_30': due_1_30,
            '31_60': due_31_60,
            '61_90': due_61_90,
            'over_90': over_90
        }

    @api.multi
    def _get_due_per_duration(self, from_dt, to_dt=False):
        f_dt = fields.Date.to_string(from_dt)
        t_dt = fields.Date.to_string(to_dt)
        invoices = self.partner_id.invoice_ids
        # get all invoices mapped to company contacts
        for child in self.partner_id.child_ids:
            invoices += child.invoice_ids

        if f_dt:
            due = invoices.filtered(
                lambda i: f_dt <= i.date_invoice <= t_dt and (i.type == 'out_invoice' or i.type=='out_refund'))
        else:
            # Invoices that are still active: Due date >= today
            due = invoices.filtered(lambda i: i.date_invoice <= t_dt and (i.type == 'out_invoice' or i.type=='out_refund'))


        due_invoices = sum(due.filtered(lambda i: i.type=='out_invoice').mapped('residual'))
        due_refunds = sum(due.filtered(lambda i: i.type=='out_refund').mapped('residual'))
        return "{0:,.2f}".format(due_invoices - due_refunds)

    @api.multi
    def _get_balance_due(self):
        due = 0.00
        balance = self.partner_id._get_overdue_amount()
        if balance > 0:
            due = balance
        return "{0:,.2f}".format(due)
