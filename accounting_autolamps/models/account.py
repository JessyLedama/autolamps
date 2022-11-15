# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions

class Account(models.Model):
    _inherit = 'account.account'

    base_for_input_tax = fields.Boolean(string = "Base for Input VAT")
    base_for_output_tax = fields.Boolean(string = "Base for Output VAT")