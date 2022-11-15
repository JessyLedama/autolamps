import logging
from openerp import api, fields, models, tools, exceptions
_logger = logging.getLogger(__name__)


class SmsHistory(models.Model):
    _name = "sms.history"
    _description = "SMS History, status"
    _order = 'create_date desc'

    state = fields.Selection(
        [('pending', "Pending"), ('sent', "Sent"), ('fail', "Failed")], default='pending')
    partner_id = fields.Many2one('res.partner', string="Customer")
    name = fields.Char('Recipient Name', required=True)
    phone = fields.Char('Mobile Number')
    date = fields.Date('Date')
    message = fields.Text('Message')
    retries = fields.Integer(default=1)
    provider_id = fields.Many2one('gateway.setup', "Provider")
    failure_reason = fields.Text("Response")

    @api.multi
    def write(self, vals):
        res = super(SmsHistory, self).write(vals)
        if 'phone' in vals:
            self.partner_id.write({
                'phone': self.phone
            })
        return res

    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] == 'sent':
                raise exceptions.Warning(
                    "You cannot delete already sent messages!")
        return super(SmsHistory, self).unlink(cr, uid, ids, context=context)

    @api.multi
    def resend_sms(self):
        self.ensure_one()
        gateway = self.provider_id
        gateway._send_sms(self.partner_id, self.phone, self.message)
        self.unlink()

