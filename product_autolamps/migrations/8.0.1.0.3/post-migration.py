from openerp import api, SUPERUSER_ID


def migrate(cr, version):
	if not version:
		return

	env = api.Environment(cr, SUPERUSER_ID, {})
	products = env['product.template'].search([])

	for prod in products:
		prod.product_sequence = env['ir.sequence'].get('product.template')

	prods = env['product.product'].search([])

	# Remove previous sequences
	prods.write({
		'product_sequence': False
	})

	# Create product.product sequence based on the template Sequence
	for this in prods:
		this.product_sequence = this.get_product_sequence()
