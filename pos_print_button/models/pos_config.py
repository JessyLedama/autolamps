# -*- coding: utf-8 -*-
import json
import os
from openerp import api, fields, models, exceptions


class PosConfig(models.Model):
    _inherit = 'pos.config'

    stock_locations = fields.Text(
        compute='_compute_stock_locations', store=True)

    @api.multi
    @api.depends('related_stock_location_ids')
    def _compute_stock_locations(self):
        for this in self:
            if this.related_stock_location_ids:
                vals = {}
                for location in this.related_stock_location_ids:

                    vals[location.id] = location.display_name
                this.stock_locations = json.dumps(vals)
