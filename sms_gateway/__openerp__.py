{
    'name': "SMS Gateway",
    'version': '0.1',
    'author': "Tritel Technologies",
    'category': 'Tools',
    'summary':'Odoo SMS Gateway via SasaSMS or Africastalking',
    'website': "http://www.tritel.co.ke",
    'depends': [
        'account_followup',
    ],
    'data': [
        'data/ir_cron.xml',
        'data/sms_template_data.xml',
        'wizard/send_sms_wizard.xml',
        'views/sms_template.xml',
        'views/sms_history.xml',
        'views/gateway_setup.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/menu.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
    'installable':True,
}
