{
    'name': 'Sale order partner addresses',
    'summary': (
        'In sale only show delivery address contacts in shipping '
        'address'
    ),
    'category': 'sale',
    'version': '15.0',
    'author': 'Armchem International Corp',
    'depends': [
        'base',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/res_partner_views.xml',
        'views/res_partner_address_view.xml',
    ],
}
