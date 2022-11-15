from openerp import api, fields, models, exceptions, _
from datetime import datetime, timedelta


class Partner(models.Model):
    _inherit = 'res.partner'

    pd_cheque_ids = fields.One2many('post.dated.cheques','partner_id')
    pd_cheques_amount = fields.Float(compute = 'compute_pd_cheque_amounts', string = 'Amount')
    balance = fields.Float()

    @api.one
    @api.depends('pd_cheque_ids','pd_cheque_ids.banked')
    def compute_pd_cheque_amounts(self):
        self.pd_cheques_amount = sum(line.amount for line in self.pd_cheque_ids if line.banked == False)

    @api.onchange('property_payment_term')
    def _onchange_property_payment_term(self):
        if self.property_payment_term:
            self.property_product_pricelist = self.property_payment_term.pricelist_id.id

    """
        Generate a ledger Report: Date | Transaction | Credit | Debit | Balance
    """
    @api.model
    def _get_str_tuple(self, list_to_convert):
        return "(" + ",".join(["'%s'" % x for x in list_to_convert]) + ")"
        # "('payable','receivable')"

    @api.model
    def _get_int_tuple(self, list_to_convert):
        return "(" + ",".join(["%i" % x for x in list_to_convert]) + ")"

    @api.multi
    def get_summary_initial_amounts(self, from_date, account_types):
        self.ensure_one()
        if not account_types:
            raise Warning(_('Account_types not in context!'))

        keys = ['debit', 'credit', 'balance']
        if not from_date:
            return dict(zip(keys, [0.0, 0.0, 0.0]))
        other_filters = " AND m.date < \'%s\'" % from_date

        partner_ids = [self.id]
        
        # append transactions attached to contacts if company
        if self.child_ids:
            partner_ids += [id for id in self.child_ids.mapped('id')]
        
        # append transactions attached to parent if this is a contact
        if self.parent_id:
            partner_ids.append(self.parent_id)
            partner_ids += [id for id in self.parent_id.child_ids.mapped('id')]


        query = """SELECT SUM(l.debit), SUM(l.credit), SUM(l.debit- l.credit)
                FROM account_move_line l
                LEFT JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_move m ON (l.move_id=m.id)
                WHERE a.type IN %s
                AND l.partner_id IN %s
                %s
                  """ % (
            self._get_str_tuple(account_types), self._get_int_tuple(partner_ids), other_filters)
        self._cr.execute(query)
        res = self._cr.fetchall()

        return dict(zip(keys, res[0]))

    @api.multi
    def get_ledger_summary(self, from_date, to_date, account_types):
        self.ensure_one()

        group_by_move = True
        if not account_types:
            raise Warning(_('Account_types not in context!'))

        other_filters = ""

        partner_ids = [self.id]
        
        # append transactions attached to contacts if company
        if self.child_ids:
            partner_ids += [id for id in self.child_ids.mapped('id')]
        
        # append transactions attached to parent if this is a contact
        if self.parent_id:
            partner_ids.append(self.parent_id.id)
            partner_ids += [id for id in self.parent_id.child_ids.mapped('id')]

        if from_date:
            other_filters += " AND m.date >= \'%s\'" % from_date
        if to_date:
            other_filters += " AND m.date <= \'%s\'" % to_date

        if group_by_move:
            select = """SELECT l.move_id,
                Max(l.date_maturity) as date_maturity,
                SUM(l.debit), SUM(l.credit),
                """
            group_by = (
                "GROUP BY m.date, l.move_id, l.currency_id")
        else:
            select = """SELECT l.move_id,
                l.date_maturity as date_maturity,
                SUM(l.debit), SUM(l.credit),
                """
            group_by = (
                "GROUP BY m.date, l.move_id, date_maturity, l.currency_id")
        query = """%s
                SUM(l.amount_currency) as amount_currency, l.currency_id
                FROM account_move_line l
                LEFT JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_move m ON (l.move_id=m.id)
                WHERE a.type IN %s
                AND l.partner_id IN %s
                %s
                %s
                ORDER BY m.date ASC, date_maturity ASC
                  """ % (
            select,
            self._get_str_tuple(account_types),
            self._get_int_tuple(partner_ids),
            other_filters,
            group_by)
        self._cr.execute(query)
        res = self._cr.fetchall()

        lines_vals = []
        balance = self.get_summary_initial_amounts(from_date, account_types)['balance'] or 0.0
        for line in res:
            line_balance = line[2] - line[3]

            if line_balance > 0:
                debit = line_balance
                credit = 0.0
            else:
                debit = 0.0
                credit = -line_balance

            balance += line_balance

            move = self.env['account.move'].browse(line[0])
            lines_vals.append({
                'move': move,
                'due': fields.Date.from_string(line[1]).strftime('%d-%m-%Y') if line[1] else "",
                'debit': debit,
                'credit': credit,
                'balance': balance,
                # For report visual purposes
                'amount': 0 - credit if credit > 0 else debit,
                'date': fields.Date.from_string(move.date).strftime('%d-%m-%Y'),
                'transaction': move.name
            })
        return lines_vals
