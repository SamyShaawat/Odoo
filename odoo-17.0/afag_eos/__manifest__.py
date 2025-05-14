# -*- coding: utf-8 -*-
{
    'name': "Afag End of Service",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_contract', 'hr_holidays', 'hr_payroll', 'afag_hr_payroll'],

    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'data/hr_eos_reason.xml',
        'data/hr_payroll_structure.xml',
        'security/ir.model.access.csv',
        'security/eos_security.xml',
        'views/hr_eos_reason_view.xml',
        'views/hr_eos_request_view.xml',
        'views/hr_leave_type_view.xml',
        'views/hr_payslip_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

