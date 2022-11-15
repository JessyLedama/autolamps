# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Autolamps",
    'summary': """
        Adds xlsx report to Purchase Orders
        """,
    'author': "Tritel Technologies Ltd",
    'website': "http://www.tritel.co.ke",
    'version': '8.0.1.0.0',
    'category': 'Purchases',
    'license': 'AGPL-3',
    'depends': [
            'purchase', 'report_xlsx',
        ],
    'data': [
        'report/purchase_order.xml',
        'views/purchase_order.xml',
        'views/product.xml',
        'security/ir.model.access.csv',
        ],
}
