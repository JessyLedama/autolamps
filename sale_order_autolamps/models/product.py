# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_template_pricelist_item_ids = fields.One2many('product.pricelist.item','product_tmpl_id')

    @api.onchange('list_price')
    def onchange_list_price(self):
        if not self.user_has_groups('autolamps_base.group_edit_prices'):
            old_price = self._origin.list_price
            new_price = self.list_price
            if old_price != new_price:
                raise exceptions.AccessError(
                    'You don\'t have Rights to change the Product Sale Price. '
                    'Contact Administrator!')

    @api.multi
    def write(self, vals):
        if 'list_price' in vals:
            if not self.user_has_groups('autolamps_base.group_edit_prices'):
                old_price = self.list_price
                new_price = vals.get('list_price', 0)
                if old_price != new_price:
                    raise exceptions.AccessError(
                        'You don\'t have Rights to change the Product Price. '
                        'Contact Administrator!')
        res = super(ProductTemplate, self).write(vals)
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_product_pricelist_item_ids = fields.One2many('product.pricelist.item','product_id')

    @api.onchange('lst_price')
    def onchange_list_price(self):
        if not self.user_has_groups('autolamps_base.group_edit_prices'):
            old_price = self._origin.lst_price
            new_price = self.lst_price
            if old_price != new_price:
                raise exceptions.AccessError(
                    'You don\'t have Rights to change the Product Price. '
                    'Contact Administrator!')

    @api.multi
    def write(self, vals):
        if 'lst_price' in vals:
            if not self.user_has_groups('autolamps_base.group_edit_prices'):
                old_price = self.lst_price
                new_price = vals.get('lst_price', 0)
                if old_price != new_price:
                    raise exceptions.AccessError(
                        'You don\'t have Rights to change the Product Price. '
                        'Contact Administrator!')
        res = super(ProductProduct, self).write(vals)
        return res
