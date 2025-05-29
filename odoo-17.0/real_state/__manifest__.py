{
    "name": "Real State",
    "version": "17.0.1.0.0",
    "category": "Extra Tools",
    "author": "Samy Mostafa Shaawat",
    "depends": ["base", "website", "mail", "sale_management", "stock", "contacts", "web_enterprise", "account",
                "account_accountant", "crm", "purchase"],
    "data": [
        "views/base_menu.xml",
        "views/property_view.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml"
    ],
    "installable": True,
    "application": True,
}
