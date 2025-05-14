from odoo import models, fields ,api

class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_percentage = fields.Float(string="Commission Percentage", default=0 ,)
    commission_liability_account_id = fields.Many2one(
        'account.account',
        string="Commission Liability Account",
        help="Account used for recording commission liabilities."
    )

    commission_payable_account_id = fields.Many2one(
        'account.account',
        string="Commission Payable Account",
        help="Account used for recording commission payables."
    )

    commission_expense_account_id = fields.Many2one(
        'account.account',
        string="Expense Account",
        help="Account used for recording commission expense."
    )

    @api.onchange('commission_percentage')
    def _onchange_commission_percentage(self):
      if self.commission_percentage:

        self.commission_percentage = self.commission_percentage