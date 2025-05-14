{
    'name': "AlShajaraa Automation Tasks",

    'summary': """        
    """,

    'description': """    """,

    'author': "Badn",
    'website': "",
    'contributors': [
        '',
    ],

    'category': 'Custom',
    'version': '17.0.1.2',
    'license': 'OPL-1',
    'depends': ['base',
                'sale_management',
                'sale',
                'purchase',
                'account_accountant',
                'project',
                'sale_project',

                ],
    'data': [
        'security/ir.model.access.csv',
        "security/security.xml",
        "reports/po_template.xml",
        "reports/rfq_template.xml",
        'data/email_template.xml',
        'views/menus_actions.xml',
        'views/inherit_sale_order_template.xml',
        'views/inherit_sale_order.xml',
        'views/inherit_project_tasks.xml',
        'data/months_data.xml',
    ],
    'qweb': [],
    'demo': [],
    'test': [],
    'css': [],
    'js': [],
    'images': [],

    'installable': True,
    'application': True,
    'auto_install': False,
}
