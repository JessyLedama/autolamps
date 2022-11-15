# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import tools
from openerp.osv import fields, osv


class LostSaleReport(osv.osv):
    _name = "lost.sale"
    _description = "Lost Sales Analysis"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'
    _columns = {
        'name': fields.char('Order Reference', readonly=True),
        'nbr': fields.integer('# of Items', readonly=True),
        'date': fields.datetime('Order Date', readonly=True),
        'product_id': fields.many2one('product.product', 'Product Variant', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True),
        'product_uom_qty': fields.float('Qty Ordered', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'product_tmpl_id': fields.many2one('product.template', 'Product', readonly=True),
        'categ_id': fields.many2one('product.category', 'Product Category', readonly=True),
        'discount': fields.float('Discount %', readonly=True),
        'order_id': fields.many2one('sale.order', 'Order #', readonly=True),
        'lost_sale_qty': fields.float(string='Sale Qty Lost', readonly=True),
        'lost_sale_amount': fields.float(string='Lost Sales Amount', readonly=True),
        'state': fields.selection([
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
        ], 'State', readonly=True)
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""create or replace view lost_sale as (
            select
                min(l.id) as id,
                count(distinct l.id) as nbr,
                s.name as name,
                s.date_order as date,
                l.product_id as product_id,
                t.uom_id as product_uom,
                l.product_uom_qty / u.factor * u2.factor as product_uom_qty,
                s.partner_id as partner_id,
                s.company_id as company_id,
                s.user_id as user_id,
                p.product_tmpl_id as product_tmpl_id,
                t.categ_id as categ_id,
                l.discount as discount,
                s.id as order_id,
                l.lost_sale_qty / u.factor * u2.factor as lost_sale_qty,
                l.lost_sale_amount as lost_sale_amount,
                s.state as state
            from
                sale_order_line l
                join sale_order s on (l.order_id=s.id)
                join res_partner partner on (s.partner_id = partner.id)
                left join product_product p on (l.product_id=p.id)
                left join product_template t on (p.product_tmpl_id=t.id)
                left join product_uom u on (u.id=l.product_uom)
                left join product_uom u2 on (u2.id=t.uom_id)
            where
                l.lost_sale_qty > 0
                and s.state in ('waiting_date', 'progress', 'manual', 'shipping_except', 'invoice_except', 'done')
            group by
                s.name,
                s.date_order,
                l.product_id,
                t.uom_id,
                l.product_uom_qty,
                s.partner_id,
                s.company_id,
                s.user_id,
                p.product_tmpl_id,
                t.categ_id,
                l.discount,
                s.id,
                l.lost_sale_qty,
                l.lost_sale_amount,
                s.state,
                u.factor,
                u2.factor 
        )""")