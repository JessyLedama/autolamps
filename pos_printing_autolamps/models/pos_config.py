from openerp import api, fields, models, exceptions


class PosConfig(models.Model):
    _inherit = 'pos.config'
    printer_name = fields.Char("Printer name", require=True)
    esd_option = fields.Boolean(string = "ESD",default=False)
