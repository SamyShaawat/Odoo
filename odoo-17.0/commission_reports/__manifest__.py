# -*- coding: utf-8 -*-

{
    'name': 'Armchem - Commission Reports - Deprecated',
    'version': '1.0',
    'author': 'Armchem International Corp',
    'category': 'Import',
    'depends': ['product', 'sale', 'sale_enterprise', 'account'],
    'description': """
    Custom Import 
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/commission_details.xml',
        'views/commission_end_of_day.xml',
        'views/commission_end_of_year.xml',
        'views/commission_total.xml',
        'views/action_clients.xml',
        'views/menus.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
        'commission_reports.assets_commission_reports': [
            ('include', 'web._assets_helpers'),
            'web/static/lib/bootstrap/scss/_variables.scss',
            ('include', 'web._assets_bootstrap'),
            'web/static/fonts/fonts.scss',
            'web/static/src/legacy/scss/list_view.scss',
        ],
        'web.assets_backend': [
            'commission_reports/static/src/js/commission_details.js',
            'commission_reports/static/src/js/commission_end_of_day.js',
            'commission_reports/static/src/js/commission_end_of_year.js',
            'commission_reports/static/src/js/commission_total.js',
            'commission_reports/static/src/js/action_manager_commission_report_dl.js',
            # 'commission_reports/static/src/scss/commission_reports.scss',
        ],
        'web.assets_qweb': [
            'commission_reports/static/src/xml/**/*',
        ],
    }
}
