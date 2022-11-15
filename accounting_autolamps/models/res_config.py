from openerp import api, fields, models

class account_config_settings(models.TransientModel):
    _inherit = 'account.config.settings'

    esd_server_address = fields.Char(string="ESD Server Address")
    esd_timeout = fields.Integer(string="ESD Timeout", default = 3)

    @api.multi
    def set_esd_server_address_defaults(self):
        return self.env['ir.values'].sudo().set_default('account.config.settings', 'esd_server_address', self.esd_server_address or "")

    @api.multi
    def set_esd_timeout_defaults(self):
        return self.env['ir.values'].sudo().set_default('account.config.settings', 'esd_timeout', self.esd_timeout or 3)