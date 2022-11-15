# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api, exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pin_number = fields.Char(string='KRA Pin')

    @api.multi
    @api.constrains('pin_number')
    def _check_pin_number(self):
        for this in self:
            if this.is_company and not \
                    this.pin_number.startswith("P"):
                raise exceptions.Warning("Company Pin Should Start with 'P..'")
