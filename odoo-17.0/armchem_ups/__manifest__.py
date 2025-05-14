# -*- coding: utf-8 -*-

{
    'name': 'Armchem - UPS',
    'version': '1.0',
    'author': 'Armchem International Corp',
    'category': 'Import',
    'depends': ['product', 'stock', 'sale', 'sale_stock', 'account', 'armchem_sale'],
    'description': """
    Build UPSWS
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/ups_security.xml',
        'views/upsws_views.xml',
        'views/upswsout_views.xml',
        'views/sale_views.xml',
        'views/menus.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
    },
}
