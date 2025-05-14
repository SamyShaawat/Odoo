# -*- coding: utf-8 -*-
#############################################################################
#    A part of Afag Project <https://www.openhrms.com>
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
from odoo import models, api, Command


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to employee loans."""
    _inherit = 'hr.payslip'


    def get_inputs(self, contract_ids, date_from, date_to):
        """Compute additional inputs for the employee payslip,
        considering active loans.
        :param contract_ids: Contract ID of the current employee.
        :param date_from: Start date of the payslip.
        :param date_to: End date of the payslip.
        :return: List of dictionaries representing additional inputs for
        the payslip."""
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from,
                                                date_to)
        employee_id = self.env['hr.contract'].browse(
            contract_ids[0].id).employee_id if contract_ids \
            else self.employee_id
        print('######################', employee_id)
        loan_id = self.env['hr.loan'].search(
            [('employee_id', '=', employee_id.id), ('state', '=', 'approve')])
        for loan in loan_id:
            for loan_line in loan.loan_lines:
                if (date_from <= loan_line.date <= date_to and
                        not loan_line.paid):
                    for result in res:
                        if result.get('code') == 'LO':
                            result['amount'] = loan_line.amount
                            result['loan_line_id'] = loan_line.id
        return res





    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        res = super(HrPayslip, self)._compute_input_line_ids()
        for slip in self:
            name = 'Loan'

            lines_to_remove = slip.input_line_ids.filtered(lambda x: x.input_type_id.code == 'LOAN')
            slip.update({'input_line_ids': [Command.unlink(line.id) for line in lines_to_remove]})

            input_type = self.env['hr.payslip.input.type'].sudo().search([]).filtered(lambda x:x.code=='LOAN')
            input_type_id = input_type.id if input_type else False
            input_line_vals={
                'name': name,
                'input_type_id': input_type_id,
            }
            loan_id = self.env['hr.loan'].search(
                [('employee_id', '=', slip.employee_id.id), ('state', '=', 'approve')])
            for loan in loan_id:
                for loan_line in loan.loan_lines.filtered(lambda x:x.date):
                    if (slip.date_from <= loan_line.date <= slip.date_to):
                        input_line_vals['amount'] = loan_line.amount
                        input_line_vals['loan_line_id'] = loan_line.id

                        slip.write({'input_line_ids':[(0,0,input_line_vals)]})
        return res



    def action_payslip_done(self):
        """ Compute the loan amount and remaining amount while confirming
            the payslip"""
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_total_amount()
        loan_flag=False
        if self.eos_id:
            for line in self.line_ids:
                if line.code == 'LOANSET' and line.total > 0:
                    loan_flag=True
            for loan in self.env['hr.loan'].sudo().search([]).filtered(lambda x:x.employee_id.id == self.employee_id.id and x.balance_amount > 0 and x.state=='approve'):
                for line in loan.loan_lines:
                    line.paid=True
                loan._compute_total_amount()

        return super(HrPayslip, self).action_payslip_done()
