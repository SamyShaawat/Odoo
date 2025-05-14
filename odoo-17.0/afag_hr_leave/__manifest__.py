# -*- coding: utf-8 -*-
{
    'name': "Afag Timeoff",

    'summary': "Timeoff Customization as per saudi arabia requirement",

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
    'depends': ['base', 'hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/hr_leave_security.xml',
        'views/hr_leave_type_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_leave_balance_view.xml',
        'data/hr_holidays_data.xml',
        'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

