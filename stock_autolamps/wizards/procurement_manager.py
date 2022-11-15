# -*- coding: utf-8 -*-

from openerp import models, fields, api

class procurement_manager(models.Model):
	_name = 'procurement.manager'

	picking_id = fields.Many2one('stock.picking')
	procurement_order_ids = fields.One2many('procurement.order','procurement_manager_id')
	state = fields.Selection([('draft',"Draft")])

class procurement_order(models.Model):
	_inherit = 'procurement.order'

	procurement_manager_id = fields.Many2one('procurement.manager')