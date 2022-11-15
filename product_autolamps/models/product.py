from openerp import api, fields, models, _


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	supplier_product_code = fields.Char(compute='compute_supplier_code', store=True)
	old_item_identifier = fields.Char(string='Old Item Id')
	measurements = fields.Char()

	product_sequence = fields.Char(
		"Product Sequence", copy=False, default="New")

	@api.model
	def create(self, vals):
		if vals.get('product_sequence', _('New')) == _('New'):
			vals['product_sequence'] = self.env['ir.sequence'].get(
				'product.product')
		return super(ProductTemplate, self).create(vals)

	@api.multi
	@api.depends('seller_ids', 'seller_ids.product_code')
	def compute_supplier_code(self):
		for product in self:
			suppliers = product.mapped("seller_ids.product_code")
			if suppliers:
				supp = [x for x in suppliers if x]
				product.supplier_product_code = ",".join(supp)

	def action_view_product_history(self, cr, uid, ids, context=None):
		act_obj = self.pool.get('ir.actions.act_window')
		mod_obj = self.pool.get('ir.model.data')
		product_ids = []
		for template in self.browse(cr, uid, ids, context=context):
			product_ids += [x.id for x in template.product_variant_ids]
		result = mod_obj.xmlid_to_res_id(cr, uid, 'stock_account.action_history_tree',raise_if_not_found=True)
		result = act_obj.read(cr, uid, [result], context=context)[0]
		result['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"
		return result


class ProductProduct(models.Model):
	_inherit = 'product.product'

	product_sequence = fields.Char("Product Sequence", copy=False)

	@api.model
	def create(self, vals):
		res = super(ProductProduct, self).create(vals)
		res.product_sequence = res.get_product_sequence()
		return res

	@api.multi
	def get_product_sequence(self):
		self.ensure_one()
		template = self.product_tmpl_id
		# FIXME: Hacky solution
		variants_with_seq = template.product_variant_ids.filtered(
			lambda a: a.product_sequence)
		temp_sequence = template.product_sequence
		sequence = 1
		if self.env.context.get('create_product_variant'):
			sequence = 0
		sequence = "%s-%s" % (temp_sequence, len(variants_with_seq)+sequence)
		return sequence

	def action_view_product_history(self, cr, uid, ids, context=None):
		result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'stock_account.action_history_tree', raise_if_not_found=True)
		result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
		result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])]"
		return result
