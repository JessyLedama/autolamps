from openerp import api, fields, models


class AccountFollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    send_sms = fields.Boolean(
        "Send SMS", default=True, help="Send a Reminder SMS")
    sms_content = fields.Text("SMS")