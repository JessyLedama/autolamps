# -*- coding: utf-8 -*-
import logging
from openerp import api, fields, models, exceptions

_logger = logging.getLogger(__name__)

class SaleWarehouseConfig(models.Model):
    _name = 'sale.warehouse'

    _sql_constraints = [
        ('warehouse_id', 'unique (warehouse_id)', 'The warehouse must be unique!'),
    ]
    
    name = fields.Char(string='Name', related='warehouse_id.name', default='New Sale Warehouse Priority')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    warehouse_priority_lines = fields.One2many('sale.warehouse.lines', 'sale_warehouse_id', string='Warehouse Priority',
     required=True)

    # TODO: Override create for name
    
    def get_priority_warehouse_ids(self):
        self.ensure_one()
        return [warehouse.warehouse_id.id for warehouse in self.warehouse_priority_lines]

    def get_priority_warehouse_route(self, warehouse):
        self.ensure_one()
        return self.warehouse_priority_lines.filtered(lambda l: l.warehouse_id == warehouse).mapped('route_id')

class SaleWarehouseConfigLines(models.Model):
    _name = 'sale.warehouse.lines'

    _sql_constraints = [('sale_warehouse_warehouse_line_uniq', 'unique (sale_warehouse_id,warehouse_id)',     
                 'Duplicate warehouses lines not allowed!')]

    sale_warehouse_id = fields.Many2one('sale.warehouse', string='Sale Warehouse', required=True, ondelete='cascade')
    # TODO: Check that warehouse cannot be repeated based on this parent_warehouse_id field
    parent_warehouse_id = fields.Many2one('stock.warehouse', string='Parent Warehouse', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    route_id = fields.Many2one('stock.location.route', string='Route', required=True)
    sequence = fields.Integer(string='Sequence')

    @api.constrains('warehouse_id')
    def _constrains_warehouse_id(self):
        if self.warehouse_id.id == self.parent_warehouse_id:
            raise exceptions.ValdationError('You cannot select the same warehouse for which you are setting a priority list.')
    
class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def get_priority_warehouse_ids(self):
        self.ensure_one()
        return self.env['sale.warehouse'].sudo().search([('warehouse_id', '=', self.id)], limit=1).get_priority_warehouse_ids()

    def get_priority_warehouse_route(self, warehouse):
        self.ensure_one()
        return self.env['sale.warehouse'].sudo().search([('warehouse_id', '=', self.id)], limit=1).get_priority_warehouse_route(warehouse)

    def check_warehouse_priority(self):
       warehouse_priority = self.env['sale.warehouse'].sudo().search([('warehouse_id', '=', self.id)], limit=1)
       return warehouse_priority