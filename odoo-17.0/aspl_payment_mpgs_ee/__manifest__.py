# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': 'Mastercard Payment Gateway Service(MPGS) Payment Acquirer (Enterprise)',
    'version': '1.1',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Account',
    'description': """Mastercard Payment Gateway Service(MPGS) Payment Acquirer""",
    'website': 'http://www.acespritech.com',
    'price': 60,
    'currency': 'EUR',
    'license': 'LGPL-3',
    'summary': 'Mastercard Payment Gateway Service(MPGS) Payment Acquirer',
    'depends': ['base', 'website_sale', 'payment'],
    'data': [
        'views/payment_mpgs_templates.xml',
        'views/payment_provider.xml',
       # 'data/payment_method_data.xml',
        'data/payment_provider_data.xml',


    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/master_card.jpg'],
    'installable': True,
    'application': True,  # Changed from 'installable' to 'application'
    'assets': {
        'web.assets_frontend': [
            'https://banquemisr.gateway.mastercard.com/static/checkout/checkout.min.js',
            "/aspl_payment_mpgs_ee/static/src/js/payment_form_mixin.js"

            # Adjust path according to your module
        ],
    },
}

