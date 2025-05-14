from odoo import models, fields, SUPERUSER_ID, api, _, exceptions
from dateutil.relativedelta import relativedelta
from datetime import datetime


class HREosRequest(models.Model):
    _inherit = 'hr.eos.request'

    # unpaid_loan_ids = fields.One2many('hr.loan', 'eos_id')
    unpaid_loan = fields.Float(compute='_compute_remaining_loans', store=True)

    # @api.onchange('employee_id')
    # def _compute_unpaid_loan(self):
    #     for rec in self:
    #         remaining_loans = self.env['hr.loan'].sudo().search([]).filtered(
    #             lambda x: x.employee_id.id == self.employee_id.id and x.balance_amount > 0 and x.state == 'approve')
    #         print(remaining_loans, '00000000000000000000000000000000000000000000')
    #         for loan in remaining_loans:
    #             vals = {
    #                 'id': loan.id,
    #                 'name': loan.name,
    #                 'balance_amount': loan.balance_amount,
    #             }
    #             rec.write(1,loan.id,{'unpaid_loan_ids'})

    @api.depends('employee_id')
    def _compute_remaining_loans(self):
        remaining_loans = self.env['hr.loan'].sudo().search([]).filtered(lambda x: x.employee_id.id == self.employee_id.id and x.balance_amount > 0 and x.state=='approve')
        remaining_amount = 0
        # print(remaining_loans, '00000000000000000000000000000000000000000000')
        for loan in remaining_loans:
            remaining_amount += loan.balance_amount
        self.unpaid_loan = remaining_amount


