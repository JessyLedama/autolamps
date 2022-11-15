# -*- coding: utf-8 -*-
{
    'name': "Sale Order Autolamps",
    'summary': """
        Sale Order specific customizations for Autolamps
        """,
    'author': "Tritel Technologies Ltd",
    'website': "http://www.tritel.co.ke",
    'version': '8.0.1.0.1',
    'category': 'Sales',
    'license': 'AGPL-3',
    'depends': [
            'approvals_customer_credit_limit',
            'sale', 
            'sale_stock', 
            'sale_commission',
            'sale_commission_product', 
            'autolamps_base',
            'stock_available_unreserved',
            'sale_sourced_by_line',
            'sale_procurement_group_by_line'
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/product_view.xml',
        'views/commissions.xml',
        'views/res_partner.xml',
        'views/sale_warehouse_config.xml',
        'views/sale_config_settings.xml',
        'views/account_followup.xml',
        'report/lost_sales_report_views.xml',
        'views/sale_sourcing_report_template.xml',
        'wizards/sale_sourcing_report_wizard.xml',
        # 'report/sale_summary_report_templates.xml',
        # 'report/sale_report.xml',
        # 'wizards/sale_report_wizard_view.xml',
        ],
}
