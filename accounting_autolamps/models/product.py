from openerp import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tax_product_ok = fields.Boolean(string="Is Tax Transaction")