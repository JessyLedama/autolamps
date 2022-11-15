from openerp import api, SUPERUSER_ID

def migrate(cr, version):
	if not version:
		return

	env = api.Environment(cr, SUPERUSER_ID, {})
	products = env['product.product'].search([])

	for prod in products:
		prod.product_sequence = env['ir.sequence'].get('product.product')
