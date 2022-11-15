from openerp import api, fields, models, tools, _


class SmsTemplate(models.Model):
    _name = "sms.template"
    _description = "SMS Template"

    name = fields.Char(required=True, string='Name')
    gateway_id = fields.Many2one(
        'gateway.setup', string='SMS Gateway')
    model_id = fields.Many2one('ir.model', string='Applies to')
    model = fields.Char(related='model_id.model', store=True)
    sms_html = fields.Text('Body', required=True)
