{
    "name": "Hospital Management",
    "version": "12.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Module for managing the Hospitals",
    "sequence": "10",
    "author": "Samy Mostafa Shaawat",
    "maintainer": "Samy Mostafa Shaawat",
    "website": "https://samy.rowad.com/",
    "depends": [
        "base",
        "website",
        "mail",
        "sale_management",
        "stock",
        "contacts",
    ],
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/patient.xml",
        "views/appointment.xml",
        "views/sale_order.xml",
        "views/template.xml",
        "views/my_appointments_template.xml",
        "reports/report.xml",
        "reports/patient_card.xml",
        "reports/appointment.xml",
    ],
    "installable": True,
    "application": True,
}
