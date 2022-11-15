import logging
import copy

from openerp import models, fields, api
# from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class stock_return_picking_line(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    all_return_id = fields.Many2one('stock.return.picking', 'All Return')


class stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    products_to_transfer = fields.Selection([
        ('all', 'All'),
        ('custom', 'Custom'),
    ], string='Products to Transfer', default='all')
    all_products = fields.Many2many('product.product', 'All Products', compute='_compute_all_products')
    product_ids = fields.Many2many(comodel_name='product.product', relation='stock_return_products', column1='return', 
    column2='products', string='Products', default=False)
    all_product_return_moves = fields.One2many('stock.return.picking.line', 'all_return_id', 'All Moves', readonly=True)
    # picking_id = fields.Many2one('stock.picking', string='Picking')

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        # pick_obj = self.pool.get('stock.picking')
        # pick = pick_obj.browse(cr, uid, record_id, context=context)
        if res.get('product_return_moves', False):
            product_return_moves = copy.deepcopy(res['product_return_moves'])
            all_moves = []
            line_obj = self.pool.get('stock.return.picking.line')
            for move in product_return_moves:
                line = line_obj.create(cr, uid, move, context=context)
                all_moves.append(line)
            res.update({'all_product_return_moves': all_moves})
        res.update(product_ids=[])
        return res

    @api.depends('all_product_return_moves')
    def _compute_all_products(self):
        for record in self:
            products = record.all_product_return_moves.mapped('product_id.id')
            record.all_products = [(6, 0, products)]

    @api.onchange('products_to_transfer')
    def _onchange_products_to_transfer(self):
        # _logger.info("original move lines %s" % self.sudo().read())
        # data = self.read(cr, uid, ids[0], context=context)
        if self.products_to_transfer == 'all' and self.product_ids:
            _logger.info("condition met")
            _logger.info("all  moves %s" % self.all_product_return_moves)
            self.product_ids = False
            self.product_return_moves = False
            # self.recreate_product_return_moves()
            # TODO: Add call to stock.act_stock_return_picking
            # pass
        # if self.products_to_transfer == 'all':
            

    def recreate_product_return_moves(self):
        action = self.env.ref('stock.act_stock_return_picking').read()[0]
        return action
        # all_product_return_moves = self.all_product_return_moves
        # _logger.info("all  moves %s" % self.all_product_return_moves)
        # product_return_moves = []
        # line_obj = self.env['stock.return.picking.line']
        # for product_return_move in all_product_return_moves:
        #     product_return_move_dict = {
        #         'product_id': product_return_move.product_id.id,
        #         'quantity': product_return_move.quantity,
        #         'move_id': product_return_move.move_id.id,
        #         # 'wizard_id': product_return_move.all_return_id.id
        #     }
        #     _logger.info('product return dict %s' % product_return_move_dict)
        #     product_return_moves.append((0, 0, product_return_move_dict))
        #     # line = line_obj.create(product_return_move_dict)
        #     # product_return_moves.append(line)
        # # self.product_return_moves = [(6, 0, product_return_moves)]
        # self.product_return_moves = product_return_moves
        # _logger.info("product return moves %s" % self.product_return_moves.mapped('id'))
        # # _logger.info("product return moves moves %s" % self.product_return_moves.mapped('move_id'))

    @api.multi
    def filter_product_return_moves(self):
        if self.product_ids:
            for product_return_move in self.product_return_moves:
                if product_return_move.product_id.id not in self.product_ids.ids:
                    self.write({
                        'product_return_moves': [(2, product_return_move.id)]
                    })
            return {
                'type': 'ir.actions.act_window',
                'name': _('Enter transfer details'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.return.picking',
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