# -*- coding: utf-8 -*-
{
    'name': "Commissions Autolamps",

    'summary': """
        Adds reporting features to commissions""",

    'description': """
        - Adds commission line views and reports on Sale Orders
        - Adds commission line views and reports on Invoices
        - Adds a commission summary report by date
        - Adds a commission settlement report by agent
        - Adds target features on agents
        - Adds grace period feature on commission
        - Adds commission line, paid commission invoice, and settlement viwes on the agent
        - Adds payable computing features to settlements based on target and grace period
        - Adds invoice summary lines on the settlemnt
    """,

    'author': "Tritel Technologies Ltd",
    'category': 'Sales Management',
    'version': '0.1',

    'depends': ['base', 'sale_commission', 'approvals_customer_credit_limit', 'account', 'sale_automatic_workflow', 'report', 'account_voucher'],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/account_invoice_views.xml',
        'wizards/agent_commission_report_wizard.xml',
        'wizards/settlement_commission_summary_report_wizard.xml',
        'views/res_partner_views.xml',
        'views/sale_commission_settlement_views.xml',
        'views/sale_commission_views.xml',
        'report/sale_order_commission_templates.xml',
        'report/account_invoice_commission_templates.xml',
        'report/commission_settlement_templates.xml',
        'report/commission_settlement_invoice_templates.xml',
        'report/agent_commission_report_templates.xml',
        'report/settlement_report_templates.xml',
        'report/commission_report.xml',
    ],
}
