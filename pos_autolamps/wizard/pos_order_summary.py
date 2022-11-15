# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import api, fields, models


class PartnerLedgerSummaryWizard(models.TransientModel):
    _name = 'pos.order.summary'
    _description = 'POS Order Summary'

    custom_filter = fields.Boolean("Custom Dates")
    from_date = fields.Date('From', default=fields.Date.today(), required=True)
    to_date = fields.Date('To', default=fields.Date.today())

    @api.multi
    def btn_print_summary(self):
        return self.env['report'].get_action(
            self, 'pos_autolamps.report_pos_order_summary')

    @api.multi
    def get_orders(self):
        domain = [('date_order', '>=', self.from_date),
                  ('state', 'in', ['paid', 'invoiced', 'done'])]
        if self.custom_filter:
            domain += [('date_order', '<=', self.to_date)]
        else:
            domain += [('date_order', '<=', self.from_date)]
        orders = self.env['pos.order'].search(domain)
        return orders

    @api.multi
    def get_order_lines(self):
        orders = self.get_orders()
        values = {
            'orders': orders,
            'taxes': self._get_tax_amount(orders),
            'payments': self._get_payments(orders),
            'total': sum(orders.mapped('amount_total'))
        }
        return values

    @api.multi
    def btn_preview_summary(self):
        self.ensure_one()
        orders = self.get_orders()
        action = self.env.ref('point_of_sale.action_pos_pos_form')
        result = action.read()[0]
        result['domain'] = [('id', 'in', orders.ids)]
        return result

    @api.multi
    def _get_tax_amount(self, orders):
        # Assume it's always one tax: VAT
        if not orders:
            return {}

        tax = orders[0].lines[0].product_id.taxes_id
        if tax:
            tax_name = tax.name
        else:
            tax_name = "VAT 16%"
        return [{
            'name': tax_name,
            'amount': sum(orders.mapped('amount_tax')),
        }]

    @api.multi
    def _get_payments(self, orders):
        if not orders:
            return {}
        _ids = orders.mapped('statement_ids.id')
        self.env.cr.execute(
            "select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
            "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
            "group by aj.name ", (tuple(_ids),))

        values = self.env.cr.dictfetchall()
        return values
