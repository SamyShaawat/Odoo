from odoo import models, fields, SUPERUSER_ID, api, _, exceptions

class HRLoanType(models.Model):
    _name = 'hr.loan.type'

    name = fields.Char(translate=True)
    company_id = fields.Many2one('res.company', required=True, string='Company', default=lambda self: self.env.company)
    payment_journal_id = fields.Many2one('account.journal')
    loan_account_id = fields.Many2one('account.account')


    _sql_constraints = [('name_unique', 'unique(name)', 'name already exists')]
