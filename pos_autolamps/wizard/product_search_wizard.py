from openerp import api, fields, models, _
# from openerp.exceptions import UserError


class ProductSearchWizard(models.TransientModel):
    _name = 'product.search'
    _description = 'Product Search'

    product_ids = fields.Many2many('product.product', string='Products')

    @api.multi
    def search_products(self):
        graph_view_ref = self.env.ref('pos_autolamps.pos_stock_quant_view_graph', False)
        tree_view_ref = self.env.ref('pos_autolamps.pos_view_stock_quant_tree', False)
        domain = []
        if len(self.product_ids)>0:
            domain = [('product_id','in',[product_id.id for product_id in self.product_ids])]
        return { 
            'name': "Product Search",
            'view_mode': 'graph, tree',
            'view_id': False,
            'view_type': 'graph',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'views': [(graph_view_ref and graph_view_ref.id or False, 'graph'),
                      (tree_view_ref and tree_view_ref.id or False, 'tree')],
            'context': {'search_default_internal_loc': 1, 'search_default_productgroup':1, 'search_default_locationgroup':1}
        }