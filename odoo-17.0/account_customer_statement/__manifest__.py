# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Customer/Supplier Statement',
    'version': '5.4.1',
    'price': 79.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Accounting & Finance',
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/account_customer_statement/778',#'https://youtu.be/scZOtAhj8co',
    'summary': 'Customer/Supplier Statement on Customer/Supplier list/form',
    'description': """
This module add report on customer/supplier form to print customer/supplier statement report same like partner ledger.
Customer/Supplier Statement
Customer Overdue Payments
Customer/Supplier Statement and Customer Overdue Payments offers you to view customers or suppliers invoice or overdue invoices details and mail customers that details
account customer statement
customer_overdue_statement
account_statement
customer statement
Account Customer/Supplier Statement
Printing Customer Statement Details
You Can Print Customer Statement Report From The Above Customer Form in Partner Form View
Sending Customer Statement Details
You Can Send Customer Statement To Relevent Customer.
helpdesk
helpdesk customer
customer ledger
customer statement report
partner statement
Probuse
partner ledger
customer ledger
supplier ledger
receivable statement
partner ledger enterprise
partner ledger filter
print partner ledger by customer
print partner ledger by supplier
print partner ledger by vendor
partner ledget option to print by partner
partner ledger
overdue customer
customer overdue
overdue payment report
overdue payment
Customer/Supplier Statements
Supplier Statements
Customer Statements
Partner wise Ledger Report
customer ledger
Customer Statement
Account Statements
Account Statement
Overdue Payments/Statement
Overdue Payments
Overdue Statement
supplier ledger
account statement
partner statement
customer statement

 """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'depends': ['account'],
    'images': ['static/description/img1.jpg'],
    'data': [
#            ACCOUNT,
        'security/ir.model.access.csv',
        'account/wizard/common_report/account_report_common_view.xml',
        'account/views/account_report.xml',
        'account/views/account_menuitem.xml',
        'account/views/report_partnerledger.xml',
        'account/wizard/account_report_partner_ledger_view.xml',
#        'account/wizard/account_report_common_view.xml',
#        'account/wizard/account_report_partner_ledger_view.xml',
        #CUSTOM
        'wizard/account_report_partner_ledger_view.xml',
        'views/report_partnerledger.xml',
        'views/report.xml',
     ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
