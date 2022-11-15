from openerp import api, fields, models

class MissingReorders(models.TransientModel):
    _name = 'missing.reorders.wizard'

    warehouse_id = fields.Many2many('stock.warehouse')

    @api.multi
    def print_missing_reorders_xlsx_report(self):
        missing_reorder_ids = self.env['stock.warehouse.orderpoint'].search([]).mapped('id')

        products = self.env['product.product'].search([('type','=','product')])

        reorders_vals = []
        warehouses = self.env['stock.warehouse'].search([])
        warehouse_ids = warehouses.mapped('id')
        warehouses_dict = {}#(warehouse.id, warehouse.name) for warehouse in warehouses {}
        for warehouse in warehouses:
            warehouses_dict[warehouse.id] = warehouse.name 
        
        for product in products:
            existing_warehouse_reorders = product.orderpoint_ids.mapped('warehouse_id')
            missing_warehouse_reorders = warehouses - existing_warehouse_reorders
            for warehouse in missing_warehouse_reorders:
                val={
                    'product_id':product.id,
                    'product_name':product.name,
                    'warehouse_id':warehouse.id,
                    'warehouse_name':warehouses_dict[warehouse.id],
                    'location_id':warehouse.lot_stock_id.id,
                    'location_name':warehouse.lot_stock_id.name,
                    'product_min_qty':0,
                    'product_max_qty':0,
                    'procurement_group_id':warehouse.resupply_procurement_group_id.id,
                    'procurement_group_name':warehouse.resupply_procurement_group_id.name,
                }

                reorders_vals.append(val)

        datas = { 
            'ids': missing_reorder_ids,
            'model': 'stock.warehouse.orderpoint',
            'form': self.read()[0],
            'reorders':reorders_vals
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'missing.reorders.xlsx',
            'datas': datas,
            'name': 'Missing Reorders Report' 
        }