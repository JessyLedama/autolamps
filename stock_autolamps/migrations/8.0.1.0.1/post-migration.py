from openerp import api, SUPERUSER_ID

def migrate(cr, version):
	if not version:
		return

	env = api.Environment(cr, SUPERUSER_ID, {})
	procurement_groups = env['procurement.group'].search([])

	if procurement_groups:
		for group in procurement_groups:
			group._compute_sale_order_group()