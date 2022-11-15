# -*- coding: utf-8 -*-
import os
from openerp import api, fields, models, exceptions


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, vals):
        if 'pos_reference' not in vals:
            sequence = self.env.ref('pos_autolamps.seq_pos_order')
            next_code = sequence.next_by_id(sequence.id)
            vals['pos_reference'] = next_code
        return super(PosOrder, self).create(vals)

    @api.one
    def get_order_sequence(self):
        sequence = self.env.ref('pos_autolamps.seq_pos_order')
        next_code = sequence.next_by_id(sequence.id)
        print(next_code)  # TODO: remove
        return {'sequence': next_code}

    def action_print_picking(self, cr, uid, ids, context=None):
        ids_list = []
        record = self.browse(cr,uid,ids[0],context=context)
        for picking in record.related_picking_id:
            ids_list.append(picking.id)
        if record.picking_id:
            ids_list.append(record.picking_id.id)
        
        return self.pool['report'].get_action(cr, uid, ids_list, 'stock.report_picking', data=None, context=context)