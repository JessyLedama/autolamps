# -*- coding: utf-8 -*-
{
    'name': "POS Autolamps",
    'summary': """
        Point of Sale Customization for Autolamps
        """,
    'author': "Tritel Technologies Ltd",
    'website': "http://www.tritel.co.ke",
    'version': '8.0.1.0.0',
    'category': 'Point of Sale',
    'license': 'AGPL-3',
    'depends': [
            'point_of_sale',
            'pos_order_summary'
        ],
    'data': [
        'data/sequence.xml',
        'views/assets_backend.xml',
        'views/pos_config.xml',
        'views/pos_order.xml',
        'views/product_view.xml',
        'wizard/product_search_wizard.xml',
        'views/pos_product_search_view.xml',
        'report/report_pos_summary.xml',
        "wizard/pos_order_summary.xml",
        ],
}
