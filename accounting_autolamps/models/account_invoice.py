from openerp import api, fields, models
import requests


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    esd_serial = fields.Char()
    sale_order_ids = fields.Many2many(
        'sale.order', 'sale_order_invoice_rel',
        'invoice_id', 'order_id', 'Sale Orders')
    direct_tax_line_ids = fields.One2many('direct.tax.lines', 'invoice_id')
    import_tax_total = fields.Float(compute='compute_import_tax')

    @api.multi
    def invoice_validate(self):
        esd = self.env['ir.values'].sudo().get_default(
            'account.config.settings', 'esd_server_address')
        if esd:
            try:
                timeout = self.env['ir.values'].sudo().get_default(
                    'account.config.settings', 'esd_timeout')
                timeout = timeout if timeout else 3
                r = requests.get(esd, timeout=timeout)
                self.esd_serial = r.text
            except:
                self.esd_serial = "###"
            res = super(account_invoice, self).invoice_validate()
            return res

    @api.one
    def set_esd(self):
        esd = self.env['ir.values'].sudo().get_default(
            'account.config.settings', 'esd_server_address')
        if esd:
            try:
                timeout = self.env['ir.values'].sudo().get_default(
                    'account.config.settings', 'esd_timeout')
                timeout = timeout if timeout else 3
                r = requests.get(esd, timeout=timeout)
                self.esd_serial = r.text
            except:
                self.esd_serial = "###"

    @api.multi
    @api.depends('type')
    def compute_import_tax(self):
        for record in self:
            if record.type == 'in_invoice':
                record.import_tax_total = sum(tax_item.amount for tax_item in record.direct_tax_line_ids)


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.model
    def create(self, vals):
        res = super(AccountInvoiceLine, self).create(vals)
        
        if vals.get('product_id',False) and res.invoice_id.type == 'in_invoice':
            product = self.env['product.product'].search([('id','=',vals['product_id'])])
            if product.tax_product_ok:
                # create tax line for input tax
                # common for input tax resulting from imports.
                # The gross amount of the line becomes the tax value to claim
                tax = {
                    'name':product.name,
                    'amount':res.price_subtotal,
                    'invoice_id':res.invoice_id.id,
                    'invoice_line_id':res.id
                    }
                self.env['direct.tax.lines'].create(tax)

        return res

    @api.multi
    def write(self, vals):
        res = super(AccountInvoiceLine, self).write(vals)

        for record in self:
            if record.product_id and record.invoice_id.type == 'in_invoice':
                product = self.env['product.product'].search([('id','=',record.product_id.id)])
                if product.tax_product_ok:
                    tax_line = self.env['direct.tax.lines'].search([('invoice_line_id','=',record.id)])
                    if tax_line:
                        tax_line.write({
                            'name':record.name,
                            'amount':record.price_subtotal
                        })
 
        return res

    @api.multi
    def unlink(self):
        tax_line = self.env['direct.tax.lines'].search([('invoice_line_id','=',self.id)])
        if tax_line:
            tax_line.unlink()
        return super(AccountInvoiceLine, self).unlink()

    

class DirectTaxLines(models.Model):
    _name = 'direct.tax.lines'

    name = fields.Char(string="Description")
    amount = fields.Float()
    invoice_id = fields.Many2one('account.invoice')
    invoice_line_id = fields.Many2one('account.invoice.line', string="Line Item")
