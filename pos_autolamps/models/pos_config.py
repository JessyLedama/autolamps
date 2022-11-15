# -*- coding: utf-8 -*-
import os
from openerp import api, fields, models, exceptions


class PosConfig(models.Model):
    _inherit = 'pos.config'

    receipt_path = fields.Char("Receipt Location", default='/opt/receipts')
    custom_sequence_id = fields.Many2one('ir.sequence', "Custom Sequence")
    last_order_id = fields.Integer(compute='_compute_last_order_id', store=True)

    @api.multi
    @api.depends('custom_sequence_id')
    def _compute_last_order_id(self):
        for this in self:
            order = self.env['pos.order'].search([])
            if order:
                this.last_order_id = order[0].id
            else:
                order = self.env['pos.order'].create({

                })
                this.last_order_id = order.id

    # @api.constrains('receipt_path')
    def _check_path(self):
        if not os.path.exists(self.receipt_path):
            raise exceptions.ValidationError("Please add a valid path!")
