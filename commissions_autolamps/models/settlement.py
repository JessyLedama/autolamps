# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class Settlement(models.Model):
    _inherit = "sale.commission.settlement"

    gross_total = fields.Float(string='Gross Total', compute='_compute_gross_total', store=True)
    total_commissionable_sales = fields.Float(string='Commissionable Sales', compute='_compute_total_commissionable_sales', store=True)
    total_valid = fields.Float(string='Valid Commissions', compute='_compute_total_valid', store=True)
    sales_over_target = fields.Float(string='Sales Above Target', compute='_compute_sales_over_target', store=True)
    agent_target = fields.Float(string='Target', related='agent.target', store=True)
    payable_factor = fields.Float(string='Payable Factor', compute='_compute_payable_factor', store=True)
    total_payable = fields.Float(string='Total Payable', compute='_compute_total_payable', store=True)
    settlement_invoices = fields.One2many(comodel_name='sale.commission.settlement.invoice', inverse_name='settlement_id', 
    string='Settlement Invoices', required=True, readonly=True)

    @api.depends('lines', 'lines.invoice_line', 'lines.invoice_line.price_subtotal')
    def _compute_gross_total(self):
        for record in self:
            record.gross_total = sum(x.invoice_line.price_subtotal for x in record.lines)
    
    @api.depends('agent_target', 'total_commissionable_sales')
    def _compute_sales_over_target(self):
        for record in self:
            record.sales_over_target = record.total_commissionable_sales - record.agent_target

    @api.depends('total_commissionable_sales', 'sales_over_target')
    def _compute_payable_factor(self):
        for record in self:
            record.payable_factor = (record.sales_over_target / (record.total_commissionable_sales or 1))
            record.payable_factor = 1 if record.payable_factor > 1 else record.payable_factor
            record.payable_factor = 0 if record.payable_factor < 0 else record.payable_factor

    @api.depends('lines', 'lines.invoice_line', 'lines.invoice_line.price_subtotal')
    def _compute_total_commissionable_sales(self):
        for record in self:
            record.total_commissionable_sales = sum(x.invoice_line.price_subtotal for x in record.lines)

    @api.depends('lines', 'lines.settled_amount')
    def _compute_total_valid(self):
        for record in self:
            record.total_valid = sum(x.settled_amount for x in record.lines)

    @api.depends('total_valid', 'payable_factor')
    def _compute_total_payable(self):
        for record in self:
            record.total_payable = record.payable_factor * record.total_valid

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = "Settlement/%s: %s - %s" % (record.agent.name, record.date_from, record.date_to)
            res.append((record.id, name))
        return res

    def _prepare_invoice_line(self, settlement, invoice_vals, product):
        invoice_line_obj = self.env['account.invoice.line']
        invoice_line_vals = {
            'product_id': product.id,
            'quantity': 1,
        }
        # Get other invoice line values from product onchange
        invoice_line_vals.update(invoice_line_obj.product_id_change(
            product=invoice_line_vals['product_id'], uom_id=False,
            type=invoice_vals['type'], qty=invoice_line_vals['quantity'],
            partner_id=invoice_vals['partner_id'],
            fposition_id=invoice_vals['fiscal_position'])['value'])
        # Put line taxes
        invoice_line_vals['invoice_line_tax_id'] = \
            [(6, 0, tuple(invoice_line_vals['invoice_line_tax_id']))]
        # Put commission fee
        invoice_line_vals['price_unit'] = settlement.total_payable
        # Put period string
        partner = self.env['res.partner'].browse(invoice_vals['partner_id'])
        lang = self.env['res.lang'].search(
            [('code', '=', partner.lang or self.env.context.get('lang',
                                                                'en_US'))])
        date_from = fields.Date.from_string(settlement.date_from)
        date_to = fields.Date.from_string(settlement.date_to)
        invoice_line_vals['name'] += "\n" + _('Period: from %s to %s') % (
            date_from.strftime(lang.date_format),
            date_to.strftime(lang.date_format))
        return invoice_line_vals


class SettlementLine(models.Model):
    _inherit = "sale.commission.settlement.line"

    product = fields.Many2one('product.product', string='Product', related='invoice_line.product_id')
    generated_invocie_id = fields.Many2one('account.invoice', string='Generated Invoice', related='settlement.invoice')
    sale_agent_line = fields.Many2one('sale.order.line.agent', string='Sale Agent Line', related='agent_line.sale_agent_line')
    sale_order = fields.Many2one('sale.order', string='Sale Order', related='sale_agent_line.sale_line.order_id')
    total_amount = fields.Float(string='Line Total', related='invoice_line.price_subtotal', store=True)
    payable = fields.Boolean(compute='_compute_payable', string='Payable', store=True, required=True, default=True)
    
    @api.depends('invoice', 'invoice.date_due', 'invoice.date_paid', 'commission', 'commission.grace_period', 'commission.invoice_state')
    def _compute_payable(self):
        for record in self:
            record.payable = True


class SettlementInvoice(models.Model):
    _name = "sale.commission.settlement.invoice"
    _description = "Sale Commission Settlement Invoices"

    settlement_id = fields.Many2one('sale.commission.settlement', string='Settlement')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    total_sales = fields.Float(string='Total Agent Sales', compute='_compute_total_sales', store=True)
    date_invoice = fields.Date(string='Date', related='invoice_id.date_invoice')
    total_commission = fields.Float(string='Total Commission')
    amount_total = fields.Float(string='Total Invoice Sales', related='invoice_id.amount_total')  # Check the invoice amount

    @api.depends('settlement_id', 'settlement_id.lines', 'settlement_id.lines.invoice', 'settlement_id.lines.invoice_line', 'settlement_id.lines.invoice_line.price_subtotal')
    def _compute_total_sales(self):
        for record in self:
            record.total_sales = sum(x.invoice_line.price_subtotal for x in self.mapped(
                'settlement_id.lines').filtered(
                lambda line: line.invoice.id == record.invoice_id.id and line.settlement.id == record.settlement_id.id))