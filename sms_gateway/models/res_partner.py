from openerp import api, fields, models, exceptions
from collections import defaultdict


class Partner(models.Model):
    _inherit = 'res.partner'

    # Send sms: payment reminders
    @api.multi
    def do_button_sms(self):
        self.ensure_one()
        phone = self.phone
        if not phone:
            phone = self.mobile
        if not phone:
            return

        level = self.latest_followup_level_id_without_lit
        if not level:
            return
        if not level.sms_content:
            return

        due_amount = self._get_overdue_amount()

        if due_amount <= 0:
            return

        sms_content = level.sms_content % {'amount': "%s" % due_amount}
        gateway = self.env['gateway.setup'].search([], limit=1)
        gateway._send_sms(self, phone, sms_content)
        # Post In Logs
        self.message_post(body=sms_content, subject="SMS Reminder")

    @api.cr_uid_ids_context
    def do_partner_mail(self, cr, uid, partner_ids, context=None):
        res = {}
        partner = self.pool.get('res.partner').browse(cr, uid, partner_ids)
        due_amount = partner._get_overdue_amount()
        # Don't send E-mail or SMS if due_amount less than 0
        if due_amount > 0:
            partner.do_button_sms()
            res = super(Partner, self).do_partner_mail(cr, uid, partner_ids, context)
        return res

    def _get_overdue_amount(self):
        company_id = self.env.user.company_id.id

        partner_ids = [self.id]
        
        # append transactions attached to contacts if company
        if self.child_ids:
            partner_ids += [id for id in self.child_ids.mapped('id')]
        
        # append transactions attached to parent if this is a contact
        if self.parent_id:
            partner_ids.append(self.parent_id.id)
            partner_ids += [id for id in self.parent_id.child_ids.mapped('id')]

        lines_per_currency = defaultdict(list)
        move_lines = self.env['account.move.line'].search([
            ('partner_id', 'in', partner_ids),
            ('account_id.type', 'in', ['payable', 'receivable']),
            ('state', '!=', 'draft'),
            ('company_id', '=', company_id),
            '|', ('date_maturity', '=', False), ('date_maturity', '<=', fields.Date.context_today(self)),
        ]) 

        # all refunds should be due even if they have a payment term
        # this list contains refunds not in move_lines
        refunds = self.env['account.move.line'].search([
            ('partner_id', 'in', partner_ids),
            ('account_id.type', 'in', ['payable', 'receivable']),
            ('state', '!=', 'draft'),
            ('company_id', '=', company_id)
        ]).filtered(lambda i: i.invoice.type=='out_refund' and i.id not in move_lines.mapped('id'))

        move_lines += refunds

        for line in move_lines:
            currency = line.currency_id or line.company_id.currency_id
            line_data = {
                'balance': line.amount_currency if currency != line.company_id.currency_id else line.debit - line.credit,
                'currency_id': currency,'customer_name':line.partner_id.name,'invoice':line.move_id.name,
            }
            lines_per_currency[currency].append(line_data)

        currency_balances = [{'balance': sum(line['balance'] for line in lines), 'currency': currency.name} for
                             currency, lines in lines_per_currency.items()]
        balance = 0.00
        for item in currency_balances:
            if item['balance'] > 0:
                balance = item['balance']
        return balance

    @api.model
    def send_sms_reminder_overdue_payments(self):
        # Defaults
        company = self.env.user.company_id
        limit = 0.00
        template = self.env.ref('sms_gateway.overdue_reminder')
        if company.overdue_payment_limit:
            limit = company.overdue_payment_limit
        if company.reminder_template_id:
            template = company.reminder_template_id
        gateway = self.env['gateway.setup'].search([], limit=1)
        for partner in self.search([('customer','=',True)]):
            due_amount = partner._get_overdue_amount()
            if due_amount > limit:
                msg = template.sms_html % {'name': partner.name, 'amount': due_amount}
                phone = partner.phone or partner.mobile
                if phone:
                    # TODO: does sasasms support BULK requests??
                    # TODO: Boolean to check if reminder has been sent, in some
                    #  scenarios where the CRON might fail, and we might need
                    #  to trigger it manually
                    gateway._send_sms(partner, phone, msg)
                    partner.message_post(body=msg, subject="SMS")
                else:
                    msg = "SMS Not send, Invalid Phone number or SMS Gateway!"
                    partner.message_post(body=msg, subject="SMS Reminder Failed")
