from openerp import api, fields, models

class Currency(models.Model):
	_inherit = 'res.currency'

	relational_rate = fields.Float(string = 'Relational Rate', compute = 'get_relational_rate', digits = (12,6))

	@api.one
	@api.depends('rate_ids','rate_ids.relational_rate')
	def get_relational_rate(self):
		rate = self.rate_ids.search([('currency_id','=',self.id)], order = 'name desc', limit=1)
		if len(rate)>0:
			self.relational_rate = rate.relational_rate

class CurrencyRate(models.Model):
	_inherit = 'res.currency.rate'

	relational_rate = fields.Float(string = "Relational Rate", digits = (12,6))

	@api.onchange('relational_rate')
	def compute_rate(self):
		# base_currency = self.env['res.currency'].search([('base','=',True)])
		if self.relational_rate > 0:
			self.rate = round((1/self.relational_rate),6)