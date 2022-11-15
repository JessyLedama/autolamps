from openerp import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    overdue_payment_limit = fields.Float("Overdue Limit", default=0.00)
    reminder_template_id = fields.Many2one(
        'sms.template', "SMS Reminder Template")
