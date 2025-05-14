# -*- coding: utf-8 -*-

{
    'name': 'Armchem - Sales',
    'version': '1.0',
    'author': 'Armchem International Corp',
    'category': 'Sales/Sales',
    'summary': 'Dynamic Commission System',
    'description': """
Pulls a commission rate from a product category, and
then adjusts per sale order line depending on price adjustments on a sale’s line.
    """,
    'depends': [
        'sale',
        'sale_management',
        'sales_team',
        'delivery',
        'armchem_product',
    ],
    'data': [
        # 'views/res_company_views.xml',
        # 'views/account_move_views.xml',
        'views/sale_views.xml',
        'views/delivery_carrier.xml',
        'views/crm_team.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'assets': {

    },
}

