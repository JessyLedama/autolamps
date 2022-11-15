import logging
import copy

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'

    products_to_transfer = fields.Selection([
        ('all', 'All'),
        ('custom', 'Custom'),
    ], string='Products to Transfer', default='all')
    all_products = fields.Many2many('product.product', 'All Products', compute='_compute_all_products')
    product_ids = fields.Many2many(comodel_name='product.product', relation='stock_transfer_products', column1='transfer_details', 
    column2='products', string='Products', default=False)
    all_item_ids = fields.One2many('stock.transfer_details_items', 'all_transfer_id', 'Items', domain=[('product_id', '!=', False)], readonly=True)

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        items = []
        packs = []
        # if not picking.pack_operation_ids:
        picking.do_prepare_partial()
        for op in picking.pack_operation_ids:
            item = {
                'packop_id': op.id,
                'product_id': op.product_id.id,
                'product_uom_id': op.product_uom_id.id,
                'quantity': op.product_qty,
                'package_id': op.package_id.id,
                'lot_id': op.lot_id.id,
                'sourceloc_id': op.location_id.id,
                'destinationloc_id': op.location_dest_id.id,
                'result_package_id': op.result_package_id.id,
                'date': op.date, 
                'owner_id': op.owner_id.id,
            }
            if op.product_id:
                items.append(item)
            elif op.package_id:
                packs.append(item)
        res.update(item_ids=items)
        res.update(packop_ids=packs)
        # if context is None: context = {}
        # res = super(stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        all_items = copy.deepcopy(res['item_ids'])
        res.update(all_item_ids=all_items)
        res.update(product_ids=[])
        return res

    @api.depends('all_item_ids')
    def _compute_all_products(self):
        for record in self:
            products = record.all_item_ids.mapped('product_id.id')
            record.all_products = [(6, 0, products)]

    @api.onchange('products_to_transfer')
    def _onchange_products_to_transfer(self):
        if self.products_to_transfer == 'all':
            self.product_ids = False
            self.item_ids = False
            self.recreate_items()

    def recreate_items(self):
        all_items = self.all_item_ids
        items = []
        for item in all_items:
            item = {
                'packop_id': item.packop_id.id,
                'product_id': item.product_id.id,
                'product_uom_id': item.product_uom_id.id,
                'quantity': item.quantity,
                'package_id': item.package_id.id,
                'lot_id': item.lot_id.id,
                'sourceloc_id': item.sourceloc_id.id,
                'destinationloc_id': item.destinationloc_id.id,
                'result_package_id': item.result_package_id.id,
                'date': item.date, 
                'owner_id': item.owner_id.id,
            }
            items.append((0, 0, item))
        self.item_ids = items

    @api.multi
    def filter_items(self):
        if self.product_ids:
            for item in self.item_ids:
                if item.product_id.id not in self.product_ids.ids:
                    self.write({
                        'item_ids': [(2, item.id)]
                    })
            return {
                'type': 'ir.actions.act_window',
                'name': _('Enter transfer details'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.transfer_details',
                'view_id': False,
                'target': 'new',
                'res_id': self.ids[0],
                'context': self.env.context,
            }
        else:
            raise ValidationError (_("There are no products selected."))

    # @api.one
    # @api.constrains('item_ids')
    # def _constrains_item_ids(self):
    #     if self.product_ids and len(self.product_ids) != len(self.item_ids):
    #         raise ValidationError (_("The products selected do not match the lines"))


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    all_transfer_id = fields.Many2one('stock.transfer_details', 'Transfer')