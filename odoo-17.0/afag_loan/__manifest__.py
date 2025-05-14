# -*- coding: utf-8 -*-
#############################################################################
#
#    Afag Technologies Pvt. Ltd.
#
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Afag Loan Management',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage Employee Loan Requests',
    'description': """This module facilitates the creation and management of employee loan requests. 
    The loan amount is automatically deducted from the salary""",
    'author': "Afag Techno Solutions,Afag",
    'company': 'Afag Techno Solutions',
    'maintainer': 'Afag Techno Solutions',
    'live_test_url': 'https://youtu.be/lAT5cqVZTZI',
    'depends': ['hr', 'account', 'afag_eos','hr_payroll'],
    'data': [
        'security/hr_loan_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/hr_loan_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_eos_request.xml',
        'data/hr_salary_rule_demo.xml',
        'data/hr_rule_input_demo.xml',
    ],
    # 'demo': ['data/hr_salary_rule_demo.xml',
    #          'data/hr_rule_input_demo.xml', ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
