# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api, exceptions


class ResCompany(models.Model):
    _inherit = 'res.company'

    etr_serial = fields.Char(string='ETR Serial')
