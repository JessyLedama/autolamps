# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import tools
import json
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)

class StockPickingType(osv.osv):
    _inherit = 'stock.picking.type'

    def _get_tristate_values_sales(self, cr, uid, ids, field_name, arg, context=None):
        picking_obj = self.pool.get('stock.picking')
        res = {}
        for picking_type_id in ids:
            #get last 10 pickings of this type
            picking_ids = picking_obj.search(cr, uid, [('picking_type_id', '=', picking_type_id), ('state', '=', 'done'), ('sale_order_group', '=', True)], order='date_done desc', limit=10, context=context)
            tristates = []
            for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
                if picking.date_done > picking.date:
                    tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('Late'), 'value': -1})
                elif picking.backorder_id:
                    tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('Backorder exists'), 'value': 0})
                else:
                    tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('OK'), 'value': 1})
            res[picking_type_id] = json.dumps(tristates)
        return res

    def _get_picking_count_sales(self, cr, uid, ids, field_names, arg, context=None):
        obj = self.pool.get('stock.picking')
        domains = {
            'count_picking_draft_sale': [('state', '=', 'draft'), ('sale_order_group', '=', True)],
            'count_picking_waiting_sale': [('state', '=', 'confirmed'), ('sale_order_group', '=', True)],
            'count_picking_ready_sale': [('state', 'in', ('assigned', 'partially_available')), ('sale_order_group', '=', True)],
            'count_picking_sale': [('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available')), ('sale_order_group', '=', True)],
            'count_picking_late_sale': [('min_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available')), ('sale_order_group', '=', True)],
            'count_picking_backorders_sale': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting', 'partially_available')), ('sale_order_group', '=', True)],
        }
        result = {}
        for field in domains:
            data = obj.read_group(cr, uid, domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', ids)],
                ['picking_type_id'], ['picking_type_id'], context=context)
            count = dict(map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
            for tid in ids:
                result.setdefault(tid, {})[field] = count.get(tid, 0)
        for tid in ids:
            if result[tid]['count_picking_sale']:
                result[tid]['rate_picking_late_sale'] = result[tid]['count_picking_late_sale'] * 100 / result[tid]['count_picking_sale']
                result[tid]['rate_picking_backorders_sale'] = result[tid]['count_picking_backorders_sale'] * 100 / result[tid]['count_picking_sale']
            else:
                result[tid]['rate_picking_late_sale'] = 0
                result[tid]['rate_picking_backorders_sale'] = 0
        return result

    _columns = {
        'count_picking_draft_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'count_picking_ready_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'count_picking_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'count_picking_waiting_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'count_picking_late_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'count_picking_backorders_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'rate_picking_late_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'rate_picking_backorders_sale': fields.function(_get_picking_count_sales,
            type='integer', multi='_get_picking_count_sales'),
        'last_done_picking_sale': fields.function(_get_tristate_values_sales,
            type='char',
            string='Last 10 Done Pickings')}
