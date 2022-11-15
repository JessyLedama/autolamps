# -*- coding: utf-8 -*-
{
    'name': "Stock Autolamps",

    'summary': """
        Adds more date search parameters to stock picking""",

    'description': """
        Adds date filters: Today, Yesterday, This Month, Last Month
    """,

    'author': "Tritel Technologies Ltd",
    'website': "http://www.tritel.co.ke",

    'category': 'Stock',
    'version': '8.0.1.0.1',

    # any module necessary for this one to work correctly
    'depends': [
                'base', 
                'product',
                'product_autolamps',
                'sms_gateway',
                'stock', 
                'stock_account',
                'report_xlsx',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'data/ir_cron.xml',
        'data/sms_template_data.xml',
        'data/courier.xml',
        'views/views.xml',
        'views/sale_picking_views.xml',
        "views/delivery_carrier.xml",
        'report/stock.xml',
        'wizards/stock_transfer_details.xml',
        'wizards/stock_return_picking_view.xml',
        'report/report_stockpicking.xml',
        'report/report_missing_reorders.xml',
        'wizards/missing_reorder_wizard.xml',
        'wizards/reorders_mass_edit_wizard.xml',
    ],
}