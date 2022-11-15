# -*- coding: utf-8 -*-
from datetime import datetime

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass

class MissingReordersTemplate(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, reorder_rule_ids):
        header = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3', 'bold': True})
        bold = workbook.add_format({'font_size': 10, 'bold': True})
        normal = workbook.add_format({'font_size': 10})
        
        # output vat
        output_sheet = workbook.add_worksheet("Missing Reorder Rules")

        # Table Headers
        row = 0
        output_sheet.write(row, 0, "product/id", bold)
        output_sheet.write(row, 1, "product_id/name", bold)
        output_sheet.write(row, 2, "warehouse_id/id", bold)
        output_sheet.write(row, 3, "warehouse_id/name", bold)
        output_sheet.write(row, 4, "location_id/id", bold)
        output_sheet.write(row, 5, "location_id/name", bold)
        output_sheet.write(row, 6, "product_max_qty", bold)
        output_sheet.write(row, 7, "product_min_qty", bold)
        output_sheet.write(row, 8, "group_id/id", bold)
        output_sheet.write(row, 9, "group_id/name", bold)

        row += 1 

        for rule in data['reorders']:
            output_sheet.write(row, 0, rule['product_id'], normal)
            output_sheet.write(row, 1, rule['product_name'], normal)
            output_sheet.write(row, 2, rule['warehouse_id'], normal)
            output_sheet.write(row, 3, rule['warehouse_name'], normal)
            output_sheet.write(row, 4, rule['location_id'], normal)
            output_sheet.write(row, 5, rule['location_name'], normal)
            output_sheet.write(row, 6, rule['product_min_qty'], normal)
            output_sheet.write(row, 7, rule['product_max_qty'], normal)
            output_sheet.write(row, 8, rule['procurement_group_id'], normal)
            output_sheet.write(row, 9, rule['procurement_group_name'], normal)


            row += 1

MissingReordersTemplate('report.missing.reorders.xlsx','product.product')