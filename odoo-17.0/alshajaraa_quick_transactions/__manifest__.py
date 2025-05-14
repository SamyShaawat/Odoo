{
    'name': "AlShajaraa Quick Transactions",

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
                'purchase'

                ],
    'data': [
        'security/ir.model.access.csv',
        "security/security.xml",
        'views/quick_transactions.xml',

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
