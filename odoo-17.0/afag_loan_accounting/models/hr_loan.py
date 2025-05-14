# -*- coding: utf-8 -*-
#############################################################################
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
from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.fields import Command


class HrLoanAcc(models.Model):
    """ Added fields for mapping account entries for loan deduction
            and installment"""
    _inherit = 'hr.loan'

    employee_account_id = fields.Many2one('account.account',
                                          string="Loan Account",
                                          help="Employee account")
    treasury_account_id = fields.Many2one('account.account',
                                          help="Treasury account for the loan",
                                          string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal",
                                 help="Journal for the loan")

    loan_type_id = fields.Many2one('hr.loan.type', ondelete='restrict')

    move_id = fields.Many2one('account.move')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange',
        copy=False, help="State of the loan request")


    def action_open_entry(self):
        self.ensure_one()
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form'
        }

    def action_recompute_installment(self):
        """This automatically create the installment the employee need to pay to
            company based on payment start date and the no of installments.
            """
        for loan in self:
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            for line in loan.loan_lines:
                if not line.paid:
                   line.date = date_start
                   date_start = date_start + relativedelta(months=1)
            loan._compute_total_amount()
        return True


    def action_deactivate(self):
        if self.activated:
            self.activated = False
            for line in self.loan_lines:
                if not line.paid:
                    line.date=''
        elif not self.activated:
            self.activated = True
            self.action_recompute_installment()




    @api.onchange('loan_type_id')
    def on_change_loan_type(self):
        for rec in self:
            rec.journal_id = rec.loan_type_id.payment_journal_id.id
            # rec.treasury_account_id = rec.loan_type_id.journal_id.id
            rec.treasury_account_id = rec.loan_type_id.payment_journal_id.default_account_id.id
            rec.employee_account_id = rec.loan_type_id.loan_account_id.id

    def action_approve(self):
        """This creates account move for request."""
        loan_approve = self.env['ir.config_parameter'].sudo().get_param(
            'account.loan_approve')
        contract_obj = self.env['hr.contract'].search(
            [('employee_id', '=', self.employee_id.id)])
        if not contract_obj:
            raise UserError('You must Define a contract for employee')
        if not self.loan_lines:
            raise UserError('You must compute installment before Approved')
        if loan_approve:
            self.write({'state': 'waiting_approval_2'})
        else:
            if (not self.employee_account_id or not self.treasury_account_id
                    or not self.journal_id):
                raise UserError(
                    "You must enter employee account & Treasury "
                    "account and journal to approve ")
            if not self.loan_lines:
                raise UserError(
                    'You must compute Loan Request before Approved')
            timenow = date.today()
            for loan in self:
                amount = loan.loan_amount
                loan_name = loan.employee_id.name
                reference = loan.name
                journal_id = loan.journal_id.id
                debit_account_id = loan.treasury_account_id.id
                credit_account_id = loan.employee_account_id.id


                credit_account_id = loan.treasury_account_id.id
                debit_account_id = loan.employee_account_id.id

                # debit_vals = {
                #     'name': loan_name,
                #     'account_id': debit_account_id,
                #     'partner_id': loan.employee_id.user_partner_id.id,
                #     'journal_id': journal_id,
                #     'date': timenow,
                #     'debit': amount > 0.0 and amount or 0.0,
                #     'credit': amount < 0.0 and -amount or 0.0,
                #     'loan_id': loan.id,
                # }
                # credit_vals = {
                #     'name': loan_name,
                #     'account_id': credit_account_id,
                #     'journal_id': journal_id,
                #     'date': timenow,
                #     'debit': amount < 0.0 and -amount or 0.0,
                #     'credit': amount > 0.0 and amount or 0.0,
                #     'loan_id': loan.id,
                # }
                # vals = {
                #     'name': 'Loan For' + ' ' + loan_name + ' - ' + loan.name,
                #     'narration': loan_name,
                #     'ref': reference,
                #     'journal_id': journal_id,
                #     'date': timenow,
                #     'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                # }
                # move = self.env['account.move'].create(vals)
                bank_suspense_account = loan.treasury_account_id.id
                move = self.env['account.move'].create(
                {
                    'move_type': 'entry',
                    # 'partner_id': loan.employee_id.user_partner_id.id,
                    # 'partner_id': loan.employee_id.address_id.id,
                    # 'date': (fields.Date.today() + timedelta(days=-20)).strftime('%Y-%m-%d'),
                    'date': timenow,
                    'ref': loan.name,
                    'journal_id': journal_id,
                    'line_ids': [
                        Command.create({'debit': amount, 'credit': 0, 'account_id': debit_account_id,
                                        'partner_id':loan.employee_id.user_id.partner_id.id, 'name':loan.name}),
                        Command.create(
                            {'debit': 0, 'credit': amount, 'account_id': bank_suspense_account, 'name':loan.name}),
                    ],
                })

                move.action_post()
                loan.move_id = move.id
            self.write({'state': 'approve'})
        return True

    def action_double_approve(self):
        """This create account move for request in case of double approval."""
        if (not self.employee_account_id or not self.treasury_account_id
                or not self.journal_id):
            raise UserError(
                "You must enter employee account & Treasury "
                "account and journal to approve ")
        if not self.loan_lines:
            raise UserError('You must compute Loan Request before Approved')
        timenow = date.today()
        for loan in self:
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            debit_account_id = loan.treasury_account_id.id
            credit_account_id = loan.employee_account_id.id

            credit_account_id = loan.treasury_account_id.id
            debit_account_id = loan.employee_account_id.id

            # debit_vals = {
            #     'name': loan_name,
            #     'account_id': debit_account_id,
            #     'partner_id': loan.employee_id.user_partner_id.id,
            #     'journal_id': journal_id,
            #     'date': timenow,
            #     'debit': amount > 0.0 and amount or 0.0,
            #     'credit': amount < 0.0 and -amount or 0.0,
            #     'loan_id': loan.id,
            # }
            # credit_vals = {
            #     'name': loan_name,
            #     'account_id': credit_account_id,
            #     'journal_id': journal_id,
            #     'date': timenow,
            #     'debit': amount < 0.0 and -amount or 0.0,
            #     'credit': amount > 0.0 and amount or 0.0,
            #     'loan_id': loan.id,
            # }
            # vals = {
            #     'name': 'Loan For' + ' ' + loan_name + ' - ' + loan.name,
            #     'narration': loan_name,
            #     'ref': reference,
            #     'journal_id': journal_id,
            #     'date': timenow,
            #     'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            # }
            # move = self.env['account.move'].create(vals)
            # move.action_post()
            bank_suspense_account = loan.treasury_account_id.id
            move = self.env['account.move'].create(
                {
                    'move_type': 'entry',
                    # 'partner_id': loan.employee_id.user_partner_id.id,
                    # 'partner_id': loan.employee_id.address_id.id,
                    # 'date': (fields.Date.today() + timedelta(days=-20)).strftime('%Y-%m-%d'),
                    'date': loan.date,
                    'ref': loan.name,
                    'journal_id': journal_id,
                    'line_ids': [
                        Command.create({'debit': amount, 'credit': 0, 'account_id': debit_account_id,
                                        'partner_id':loan.employee_id.user_id.partner_id.id, 'name':loan.name}),
                        Command.create(
                            {'debit': 0, 'credit': amount, 'account_id': bank_suspense_account, 'name':loan.name}),
                    ],
                })

            move.action_post()
            loan.move_id = move.id
        self.write({'state': 'approve'})
        return True


class HrLoanLineAcc(models.Model):
    """ Creating account move for while confirm the loan lines"""
    _inherit = "hr.loan.line"

    def action_paid_amount(self, month):
        """This creates the account move line for payment of each installment.
            """
        timenow = date.today()
        for line in self:
            if line.loan_id.state != 'approve':
                raise UserError("Loan Request must be approved")
            amount = line.amount
            loan_name = line.employee_id.name
            reference = line.loan_id.name
            journal_id = line.loan_id.journal_id.id
            debit_account_id = line.loan_id.employee_account_id.id
            credit_account_id = line.loan_id.treasury_account_id.id
            name = 'LOAN/' + ' ' + loan_name + '/' + month
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            }
            vals = {
                'name': name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
        return True
