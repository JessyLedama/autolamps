from openerp import api, SUPERUSER_ID

def migrate(cr, version):
	if not version:
		return

	env = api.Environment(cr, SUPERUSER_ID, {})
	sale_order_lines = env['sale.order.line'].search([])

	if sale_order_lines:
		for line in sale_order_lines:
			if line.product_original_qty == False or line.product_original_qty == 0:
				line.product_original_qty = line.product_uom_qty or line.product_uos_qty
			line._compute_lost_sale_qty()
			line._compute_lost_sale_amount()