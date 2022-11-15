from openerp import api, fields, models

class ProductProduct(models.Model):
    _inherit='product.product'

    @api.multi
    def action_view_pos_sales(self):
        action = self.env.ref("pos_autolamps.act_pos_order_lines").read()[0]
        action["context"] = {
            "search_default_product_id": self.id,
        }
        
        return action

class ProductTemplate(models.Model):
    _inherit='product.template'

    @api.multi
    def action_view_pos_sales(self):
        action = self.env.ref("pos_autolamps.act_pos_order_lines").read()[0]
        action['domain'] = [('product_id.product_tmpl_id','=',self.id)]
        
        return action