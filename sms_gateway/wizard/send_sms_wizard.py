# -*- coding: utf-8 -*-
from openerp import api, fields, models


class SendSmsWizard(models.TransientModel):
    _name = 'send.sms.wizard'
    _description = "Send SMS Wizard"

    partner_id = fields.Many2one('res.partner')
    phone = fields.Char("Phone", required=True)
    use_template = fields.Boolean("Use Template")
    template_id = fields.Many2one('sms.template', "SMS Template")
    body = fields.Text("SMS Body", required=True)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            # Only supporting name & Amount
            # due_amount = self.partner_id.payment_amount_due
            sms_template = self.template_id.sms_html
            vals = {
                'name': self.partner_id.name
            }
            if 'amount' in sms_template:
                due_amount = self.partner_id._get_overdue_amount()
                vals['amount'] = "%s" % due_amount

            sms_content = sms_template % vals
            self.body = sms_content

    @api.multi
    def btn_send_sms(self):
        self.ensure_one()
        gateway = self.env['gateway.setup'].search([], limit=1)
        phone = self.phone
        sms = self.body
        gateway._send_sms(self.partner_id, phone, sms)
        # Post In Logs
        self.partner_id.message_post(body=sms, subject="SMS")