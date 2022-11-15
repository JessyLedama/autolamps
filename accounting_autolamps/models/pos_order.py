from openerp import api, fields, models

class pos_order(models.Model):
	_inherit = 'pos.order'

	amount_untaxed = fields.Float(string="Subtotal", compute="_compute_amount_untaxed")

	@api.one
	@api.depends('lines.price_subtotal')
	def _compute_amount_untaxed(self):
		for record in self:
			if record.lines:
				self.amount_untaxed = sum(line.price_subtotal for line in record.lines)