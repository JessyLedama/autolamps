from openerp import api, fields, models

class MassEditReorders(models.TransientModel):
	_name = 'mass.edit.reorders.wizard'

	warehouse_ids = fields.Many2many('stock.warehouse', required=True)
	action = fields.Selection([('activate',"Activate"),('deactivate',"Deactivate")], required=True)

	@api.multi
	def mass_edit_reorders(self):
		domain = [('warehouse_id','in',self.warehouse_ids.mapped('id'))]
		if self.action == 'activate':
			domain.append(('active','=',False)) 
		
		reorder_ids = self.env['stock.warehouse.orderpoint'].search(domain)

		if reorder_ids:
			if self.action == 'activate':
				reorder_ids.write({'active':True})
			elif self.action == 'deactivate':
				reorder_ids.write({'active':False})
