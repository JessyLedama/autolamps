# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    landed_cost_factor = fields.Float()
    base_pricing_factor = fields.Float()
    pricing_preference = fields.Selection([
        ('strict',"Strict"),
        ('high',"Prefer higher Price"),
        ('low',"Prefer Lower Price")
        ])
    costing_ids = fields.One2many('purchase.costing','order_id')
    cost_item_ids = fields.One2many('purchase.costing.item.lines','order_id')
    cost_items_amount_total = fields.Float(compute='_compute_cost_items_totals')
    cost_base_amount = fields.Float(compute='_compute_cost_items_totals')
    cost_base_amount_lcy = fields.Float(compute='_compute_cost_items_totals')
    currency_factor = fields.Float(string='Currency Rate', default=1)

    @api.multi
    def print_xlsx_report(self):
        datas = {
            'ids': self.ids,
            'model': 'purchase.order',
            'form': self.read()[0]
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'purchase.order.xlsx',
            'datas': datas,
            'name': 'Purchase Order'
        }

    @api.multi
    def compute_costing_lines(self):
        self.costing_ids.unlink()
        lines = []
        for record in self:
            for line in record.order_line:
                val = {}
                val['product_id'] = line.product_id
                val['old_cost'] = line.product_id.standard_price
                landed_cost = self.landed_cost_factor * (self.currency_factor or 1) * line.price_unit if self.landed_cost_factor > 0 else line.product_id.standard_price
                val['new_cost'] = landed_cost
                val['old_price'] = line.product_id.lst_price
                price = self.base_pricing_factor * landed_cost if self.base_pricing_factor > 0 else line.product_id.lst_price
                
                val['computed_price'] = price
                
                if self.pricing_preference == "high":
                    val['new_price'] = round(price if price > line.product_id.lst_price else line.product_id.lst_price)
                elif self.pricing_preference == "low":
                    val['new_price'] = round(price if price < line.product_id.lst_price else line.product_id.lst_price)
                else:
                    val['new_price'] = round(price)

                val['new_price'] = round(float(val['new_price'])/10)*10 #round to nearest 10. Make sure price is a float for correct computation
                val['old_margin'] = line.product_id.lst_price - line.product_id.standard_price
                val['new_margin'] = val['new_price'] - val['new_cost']

                val['cost_difference'] = val['new_cost'] - val['old_cost']
                val['price_difference'] = val['new_price'] - val['old_price']

                lines.append((0, 0, val))

        self.costing_ids = lines

    @api.multi
    def adjust_costing(self):
        for record in self:
            for line in record.costing_ids:
                line.product_id.lst_price = line.new_price
                line.product_id.standard_price = line.new_cost

    @api.multi
    def revert_costing(self):
        for record in self:
            for line in record.costing_ids:
                line.product_id.lst_price = line.old_price
                line.product_id.standard_price = line.old_cost

    @api.one
    def update_supplier_pricelist(self):
        for product in self.order_line:
            supplier_pricelist = product.product_id.seller_ids.filtered(lambda x: x.name.id == self.partner_id.id)
            if len(supplier_pricelist)>0:
                for pricelist in supplier_pricelist:
                    pricelist.purchase_id = self.id
                    for line in pricelist.pricelist_ids:
                        line.price = product.price_unit

    @api.multi
    @api.depends('amount_total','cost_item_ids.amount','currency_factor')
    def _compute_cost_items_totals(self):
        for order in self:
            order.cost_items_amount_total = sum(cost_item.amount for cost_item in order.cost_item_ids)
            order.cost_base_amount = order.amount_total
            order.cost_base_amount_lcy = order.amount_total * order.currency_factor if order.currency_factor > 0 else order.amount_total

    @api.multi
    def btn_compute_landed_cost_factor(self):
        self.ensure_one()
        self.landed_cost_factor = (1 + self.cost_items_amount_total/self.cost_base_amount_lcy)

class PurchaseCosting(models.Model):
    _name = "purchase.costing"

    order_id = fields.Many2one('purchase.order')
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    old_cost = fields.Float(string="Old Cost", readonly=True)
    new_cost = fields.Float(string="New Cost", readonly=True)
    old_price =fields.Float(string="Old Price", readonly=True)
    computed_price = fields.Float(string='Computed Price', readonly=True)
    new_price = fields.Float(string="New Price")
    old_margin = fields.Float(string="Old Margin", readonly=True)
    new_margin = fields.Float(string="New Margin", readonly=True)
    cost_difference = fields.Float(string="Cost Difference", readonly=True)
    price_difference = fields.Float(string="Price Difference", readonly=True)

    @api.onchange('new_price')
    def _recompute_price_and_margin(self):
        self.new_margin = self.new_price - self.new_cost
        self.price_difference = self.new_price - self.old_price

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    purchase_id = fields.Many2one('purchase.order', string="Last updated By PO", readonly=True)

class PurchaseCostingItem(models.Model):
    _name = 'purchase.costing.item'

    name = fields.Char()

class PurchaseCostingItemLines(models.Model):
    _name = 'purchase.costing.item.lines'

    costing_item_id = fields.Many2one('purchase.costing.item', string='Cost Item')
    amount = fields.Float()
    order_id = fields.Many2one('purchase.order')
