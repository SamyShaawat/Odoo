# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Generate Customer Unique Reference',
    'version': '17.0.0.0',
    'category': 'Sales',
    'summary': 'Generate Customer Unique code Generate Customer Reference Generate Customer code Unique code for customer Unique Reference for customer pos customer unique code pos unique code for customer pos unique ref for customer create unique code for customer code',
    'description': """
        this odoo app helps user to generate and identify each customer with unique reference , User can also search customer using this unique reference in backend also in point of sale. 
    """,
    'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_customer_ref_unique_code&version=17&edition=Community',
    "price": 7,
    "currency": 'EUR',
    'depends': ['point_of_sale', 'contacts'],
    'data': [
        'data/customer_unique_sequence.xml',
        'views/res_config_setting_views.xml',
        'views/res_partner_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bi_customer_ref_unique_code/static/src/js/db.js',
            'bi_customer_ref_unique_code/static/src/xml/Screens/ClientListScreen/ClientLine.xml',
            'bi_customer_ref_unique_code/static/src/xml/Screens/ClientListScreen/ClientListScreen.xml'
        ],
    },
    'installable': True,
    'auto_install': False,
    "license":'OPL-1',
    'live_test_url': 'https://www.browseinfo.com/demo-request?app=bi_customer_ref_unique_code&version=17&edition=Community',
    "images":['static/description/Banner.gif'],
}
