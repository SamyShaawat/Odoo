#######################################################################

#######################################################################

{
    'name': 'commission report',
    'author': ' ',
    'website': 'http://www.google.com',
    'description': "A module that customizes the accounting module. customize by AMB",
    'depends': ['account', 'sale_management', 'account_accountant'],
    'category': 'Accounting',
    'data': [

        'security/ir.model.access.csv',
        'wizard/invoice_commission_report.xml',
        'wizard/template.xml',
        'views/sale_order.xml',

    ],
    "installable": True,
    'installable': True,
    "application": False,
    "version": "0.0.1",
}
