# -*- coding: utf-8 -*-
from openerp import api, fields, models, exceptions


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    payment_term_ids = fields.One2many('account.payment.term', 'pricelist_id')
