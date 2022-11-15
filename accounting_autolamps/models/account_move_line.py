# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions 

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def print_xlsx_report(self):
        datas = {
            'ids': self.ids,
            'model': 'account.move.line',
            'form': self.read()[0]
        } 

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'report.vat.xlsx',
            'datas': datas,
            'name': 'VAT Report'
        }

class VATReportWizard(models.TransientModel):
    _name = "vat.report.wizard"

    start_date = fields.Date()
    end_date = fields.Date()
    sales_account_ids = fields.One2many('vat.output.account.lines','vat_wizard_id')
    purchase_account_ids = fields.One2many('vat.input.account.lines','vat_wizard_id')
    input_accounts = fields.Char(compute = 'compute_accounts')
    output_accounts = fields.Char(compute = 'compute_accounts')

    @api.multi
    def print_xlsx_report(self):
        purchase_accounts = self.purchase_account_ids.mapped("account_id.id")
        sales_accounts = self.sales_account_ids.mapped("account_id.id")
        accounts = purchase_accounts + sales_accounts

        move_lines = self.env['account.move.line'].search([
            ('account_id','in', accounts)
            ]).filtered(lambda r: r.move_id.state == "posted").mapped('id')

        datas = {
            'ids': move_lines,
            'model': 'account.move.line',
            'form': self.read()[0]
        } 

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'vat.xlsx',
            'datas': datas,
            'name': 'VAT Report'
        }

    @api.multi
    @api.depends('purchase_account_ids','purchase_account_ids.account_id','sales_account_ids','sales_account_ids.account_id')
    def compute_accounts(self):
        for report in self:
            purchases = self.purchase_account_ids.mapped('account_id.id')
            purchases_accounts = [str(x) for x in purchases]
            self.input_accounts = ",".join(purchases_accounts)

            sales = self.sales_account_ids.mapped('account_id.id')
            sales_accounts = [str(x) for x in sales]
            self.output_accounts = ",".join(sales_accounts)

    @api.onchange('start_date','end_date')
    def get_accounts(self):
        self.purchase_account_ids.unlink()
        self.sales_account_ids.unlink()

        purchase_accounts_lines = []
        purchase_accounts = self.env['account.account'].search([('base_for_input_tax','=',True)])
        for account in purchase_accounts:
            val = {
                'vat_wizard_id':self.id,
                'account_id':account.id
            }
            purchase_accounts_lines += [val]

        sales_accounts_lines = []
        sales_accounts = self.env['account.account'].search([('base_for_output_tax','=',True)])
        for account in sales_accounts:
            val = {
                'vat_wizard_id':self.id,
                'account_id':account.id
            }
            sales_accounts_lines += [val]

        self.update({'purchase_account_ids':purchase_accounts_lines, 'sales_account_ids':sales_accounts_lines})

class VATOutputAccounts(models.TransientModel):
    _name = 'vat.output.account.lines'

    vat_wizard_id = fields.Many2one('vat.report.wizard')
    account_id = fields.Many2one('account.account', string = "Account")

class VATInputAccounts(models.TransientModel):
    _name = 'vat.input.account.lines'

    vat_wizard_id = fields.Many2one('vat.report.wizard')
    account_id = fields.Many2one('account.account', string = "Account")