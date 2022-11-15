from openerp import api, SUPERUSER_ID

def migrate(cr, version):
	if not version:
		return

	env = api.Environment(cr, SUPERUSER_ID, {})
	products = env['product.template'].search([])

	if products:
		products._recompute_todo(products[0]._fields['supplier_product_code'])