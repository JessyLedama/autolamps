# -*- coding: utf-8 -*-
{
    'name': "Product Autolamps",
    'summary': """
        Contains Specific Product customizations for Autolamps Products
        """,
    'author': "Tritel Technologies Ltd",
    'website': "http://www.tritel.co.ke",
    'version': '8.0.1.0.3',
    'category': 'Product',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'website_sale',
        'report_xlsx',
        'stock',
    ],
    'data': [
        'data/sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_view.xml',
    ],
}
