from openerp import api, fields, models


class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    default_workflow_id = fields.Many2one(
        'sale.workflow.process', "Default Sale Order Workflow")

    @api.multi
    def set_default_workflow_id(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'default_workflow_id',
            self.default_workflow_id.id)
