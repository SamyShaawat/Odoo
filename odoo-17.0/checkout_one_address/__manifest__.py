# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Checkout One Address',
    'category': 'Website',
    'sequence': 1,
    'summary': 'Only one addess is set for billing and shipping, customer is not allowed to choose different address for shipping and billing.',
    'website': 'http://www.odoo.com/',
    'version': '1.0',
    'authore': 'MadeUp Infotech',
    'description': """
Only one addess is set for billing and shipping, customer is not allowed to choose different address for shipping and billing.
        """,
    'depends': ['website_sale'],
    'installable': True,
    'data': [
        'data/data.xml',
        'views/templates.xml',
    ],
    'application': True,
}
