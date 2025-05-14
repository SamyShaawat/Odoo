# -*- coding: utf-8 -*-

{
    'name': 'Armchem - Products & Pricelists',
    'version': '1.0',
    'author': 'Armchem International Corp',
    'category': 'Sales/Sales',
    'depends': ['product'],
    'description': """
This is the base module for managing commission in Odoo.
========================================================================
Adds the following fields in product category form
    1). Category commission,
    2). Maximum Discount
    """,
    'data': [
        'security/product_security.xml',
        'views/product_views.xml',
        'views/product_pricelist_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
    },
}
