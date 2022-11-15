# -*- coding: utf-8 -*-
from openerp import fields, models, api


class DeliveryCourier(models.Model):
    _name = 'delivery.courier'
    _description = 'Delivery Couriers'

    name = fields.Char(required=True)
    code = fields.Char("Abbreviation", required=True)
