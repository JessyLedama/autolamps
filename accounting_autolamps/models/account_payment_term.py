# -*- coding: utf-8 -*-
from openerp import api, fields, models, exceptions


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    pricelist_id = fields.Many2one('product.pricelist', "Pricelist")

