{
    'name': 'Pay Commission',
    'version': '17.0.0.0.0',
    'author': 'BADN',
    'category': 'Sales',
    'depends': ['sale', 'account'],
    'data': [

        'views/sale_order.xml',
        'views/res_company.xml',
        'views/purchase_order.xml',
        'views/employee_commission.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'post_init_hook': 'create_journal',
}
