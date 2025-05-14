# -*- coding: utf-8 -*-
#############################################################################
#
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
    'name': 'Afag Loan Accounting',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Afag Loan Accounting',
    'description': """Create accounting entries for loan requests.""",
    'depends': [
        'hr_payroll', 'hr', 'account', 'afag_loan',
    ],
    'data': [
        'security/ohrms_loan_accounting_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/hr_loan_type_view.xml',
        'views/hr_loan_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
