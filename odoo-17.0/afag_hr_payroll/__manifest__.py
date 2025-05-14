# -*- coding: utf-8 -*-
{
    'name': "Afag Payroll Customization",

    'summary': "Payroll Customization as per saudi arabia",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'l10n_sa_hr_payroll'],

    # always loaded
    'data': [
        'data/hr_settlement.xml',
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_settlement.xml',
        'views/hr_settlement_type.xml',
        'views/hr_contract.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

