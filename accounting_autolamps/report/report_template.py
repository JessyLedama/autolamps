# -*- coding: utf-8 -*-
from datetime import datetime
import itertools
# import pandas as pd

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass

class AccountReportVATXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, move_lines):
        header = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3', 'bold': True})
        bold = workbook.add_format({'font_size': 10, 'bold': True})
        normal = workbook.add_format({'font_size': 10})
        
        # output vat
        output_sheet = workbook.add_worksheet("Sales Output Template")

        # Table Headers
        row = 0
        output_sheet.write(row, 0, "PIN OF PURCHASER", bold)
        output_sheet.write(row, 1, "NAME OF PURCHASER", bold)
        output_sheet.write(row, 2, "ETR SERIAL NUMBER", bold)
        output_sheet.write(row, 3, "INVOICE DATE", bold)
        output_sheet.write(row, 4, "INVOICE NUMBER", bold)
        output_sheet.write(row, 5, "DESCRIPTION OF GOODS", bold)
        output_sheet.write(row, 6, "TAXABLE VALUE", bold)
        output_sheet.write(row, 7, "", bold)
        output_sheet.write(row, 8, "RELEVANT INVOICE NUMBER", bold)
        output_sheet.write(row, 9, "RELEVANT INVOICE DATE", bold)

        row += 1
        etr_serial = self.env.user.company_id.etr_serial
        
        # output invoices
        domain_invoices = []
        if data['form']['start_date']:
            domain_invoices.append(('date_invoice','>=',data['form']['start_date']))

        if data['form']['end_date']:
            domain_invoices.append(('date_invoice','<=',data['form']['end_date']))
        
        domain_invoices.append(('state','in',['open','paid']))
        domain_invoices.append(('type', 'in', ['out_invoice','out_refund']))

        invoices = self.env['account.invoice'].search(domain_invoices)
        for invoice in invoices:
            output_sheet.write(row, 0, invoice.partner_id.pin_number, normal)
            output_sheet.write(row, 1, invoice.partner_id.name, normal)
            output_sheet.write(row, 2, etr_serial, normal)
            output_sheet.write(row, 3, datetime.strptime(invoice.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y"), normal)
            output_sheet.write(row, 4, invoice.number, normal)
            output_sheet.write(row, 5, "Motor Vehicle Spares", normal)
            amount_untaxed = invoice.amount_untaxed if invoice.type == 'out_invoice' else invoice.amount_untaxed * -1
            output_sheet.write(row, 6, amount_untaxed, normal)
            output_sheet.write(row, 7, "", normal) # blank before refunds
            # refunds
            if invoice.type == 'out_refund':
                refunded_invoice_move = invoice.payment_ids.filtered(lambda x : x.invoice.type == 'out_invoice')
                if len(refunded_invoice_move)>0:
                    refunded_invoice = refunded_invoice_move[0].invoice
                    output_sheet.write(row, 8, refunded_invoice.number, normal) # relevant invoice number
                    output_sheet.write(row, 9, datetime.strptime(refunded_invoice.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y"), normal) # relevant invoice date

            row += 1

        # pos sales
        # implement any filters available on data['form']
        domain_pos = []
        if data['form']['start_date']:
            domain_pos.append(('date_order','>=',data['form']['start_date']))

        if data['form']['end_date']:
            domain_pos.append(('date_order','<=',data['form']['end_date']))
        
        orders = self.env['pos.order'].search(domain_pos)

        for order in orders:
            output_sheet.write(row, 0, order.partner_id.pin_number, normal)
            output_sheet.write(row, 1, order.partner_id.name, normal)
            output_sheet.write(row, 2, etr_serial, normal)
            output_sheet.write(row, 3, datetime.strptime(order.date_order,"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"), normal)
            output_sheet.write(row, 4, order.pos_reference, normal)
            output_sheet.write(row, 5, "Motor Vehicle Spares", normal)
            output_sheet.write(row, 6, order.amount_untaxed, normal)
            output_sheet.write(row, 7, "", normal) # blank before refunds
            
            # refunds
            # search for the related pos order and add details to
            # relevant order number and relevant order date
            if order.amount_untaxed < 0:
                refunded_order = self.env['pos.order'].search([
                    ('id','=',order.original_order_id.id),
                    ('state','in',['invoiced','paid','done']),
                    ])
                if len(refunded_order)>0:
                    output_sheet.write(row, 8, refunded_order.pos_reference, normal) # relevant invoice number
                    output_sheet.write(row, 9, datetime.strptime(refunded_order.date_order,"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"), normal) # relevant invoice date

            row += 1


        # input vat
        input_sheet = workbook.add_worksheet("Purchase Input Template")

        # Table Headers
        row = 0
        input_sheet.write(row, 0, "TYPE OF PURCHASES", bold)
        input_sheet.write(row, 1, "PIN OF SUPPLIER", bold)
        input_sheet.write(row, 2, "NAME OF SUPPLIER", bold)
        input_sheet.write(row, 3, "INVOICE DATE", bold)
        input_sheet.write(row, 4, "INVOICE NUMBER", bold)
        input_sheet.write(row, 5, "DESCRIPTION OF GOODS", bold)
        input_sheet.write(row, 6, "TAXABLE VALUE", bold)
        input_sheet.write(row, 7, "", bold)
        input_sheet.write(row, 8, "RELEVANT INVOICE NUMBER", bold)
        input_sheet.write(row, 9, "RELEVANT INVOICE DATE", bold)

        row += 1
        
        # input invoices
        domain_input_invoices = []
        if data['form']['start_date']:
            domain_input_invoices.append(('date_invoice','>=',data['form']['start_date']))

        if data['form']['end_date']:
            domain_input_invoices.append(('date_invoice','<=',data['form']['end_date']))
        
        domain_input_invoices.append(('state','in',['open','paid']))
        domain_input_invoices.append(('type', 'in', ['in_invoice','in_refund']))

        input_invoices = self.env['account.invoice'].search(domain_input_invoices)
        for invoice in input_invoices:
            if invoice.amount_tax > 0:
                input_sheet.write(row, 0, invoice.partner_id.pin_number, normal)
                input_sheet.write(row, 1, invoice.partner_id.name, normal)
                input_sheet.write(row, 2, etr_serial, normal)
                input_sheet.write(row, 3, datetime.strptime(invoice.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y"), normal)
                input_sheet.write(row, 4, invoice.number, normal)
                input_sheet.write(row, 5, "Invoice Purchases", normal)
                amount_untaxed = invoice.amount_untaxed if invoice.type == 'in_invoice' else invoice.amount_untaxed * -1
                input_sheet.write(row, 6, amount_untaxed, normal)
                input_sheet.write(row, 7, "", normal) # blank before refunds
                # refunds
                if invoice.type == 'in_refund':
                    refunded_invoice_move = invoice.payment_ids.filtered(lambda x : x.invoice.type == 'in_invoice')
                    if len(refunded_invoice_move)>0:
                        refunded_invoice = refunded_invoice_move[0].invoice
                        input_sheet.write(row, 8, refunded_invoice.number, normal) # relevant invoice number
                        input_sheet.write(row, 9, datetime.strptime(refunded_invoice.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y"), normal) # relevant invoice date

                row += 1

            # consider taxes arising from invoices with import tax
            if invoice.import_tax_total > 0:
                input_sheet.write(row, 0, invoice.partner_id.pin_number, normal)
                input_sheet.write(row, 1, invoice.partner_id.name, normal)
                input_sheet.write(row, 2, etr_serial, normal)
                input_sheet.write(row, 3, datetime.strptime(invoice.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y"), normal)
                input_sheet.write(row, 4, invoice.number, normal)
                input_sheet.write(row, 5, "Tax from Import Purchases", normal)
                amount_untaxed = invoice.amount_untaxed if invoice.type == 'in_invoice' else invoice.amount_untaxed * -1
                # input_sheet.write(row, 6, invoice.import_tax_total, normal)
                input_sheet.write(row, 7, invoice.import_tax_total, normal) # blank before refunds
                # refunds
                # if invoice.type == 'in_refund':
                #     refunded_invoice_move = invoice.payment_ids.filtered(lambda x : x.invoice.type == 'in_invoice')
                #     if len(refunded_invoice_move)>0:
                #         refunded_invoice = refunded_invoice_move[0].invoice
                #         input_sheet.write(row, 8, refunded_invoice.number, normal) # relevant invoice number
                #         input_sheet.write(row, 9, datetime.strptime(refunded_invoice.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y"), normal) # relevant invoice date

                row += 1



AccountReportVATXlsx('report.vat.xlsx','account.move.line')