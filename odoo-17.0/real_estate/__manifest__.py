{
    "name": "Real Estate",
    "version": "17.0.1.0.0",
    "category": "Custom Apps",
    'summary': 'Real Estate Management',
    'description': 'Manage properties, offers, buyers, sellers. Custom app for real estate workflows.',
    "author": "Samy Mostafa Shaawat",
    "depends": [
        "base",
        "website",
        "mail",
        "sale_management",
        "stock",
        "contacts",
        "web_enterprise",
        "account",
        "account_accountant",
        "crm",
        "purchase"
    ],
    "data": [
        "views/base_menu.xml",
        "views/property_view.xml",
        "views/owner_view.xml",
        "views/tag_view.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "application": True,
    'license': 'OEEL-1',
}
