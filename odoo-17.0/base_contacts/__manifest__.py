# -*- coding: utf-8 -*-


{
    'name': 'Contacts',
    'category': 'Commission',
    'sequence': 150,
    'summary': 'Centralize your address book',
    'description': """
This module generates uniqe custoer id and vendor id
""",
    'depends': ['base', 'mail', 'account'],
    'data': [
        'data/ir_sequence_data.xml',
        'data/service_cron.xml',
        'views/res_partner_views.xml',
    ],
    'application': True,
}
