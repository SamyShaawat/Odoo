# -*- coding: utf-8 -*-

#from openerp import fields, models, _, api
#from openerp.exceptions import UserError
from odoo import fields, models, _, api
from odoo.exceptions import UserError


class AccountPartnerLedgerStatement(models.TransientModel):
    _inherit = "account.report.partner.ledger"
    _name = "account.report.partner.ledger.statement"
    _description = "Account Customer Statement"

#    @api.multi
    def check_report_excel(self):
        raise UserError(
            _('Not Implemented!'))

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({
            'reconciled': self.reconciled,
            'amount_currency': self.amount_currency,
            'custom_partner_ids':self.env.context.get('active_ids')
        })
        return self.env.ref('account_customer_statement.action_report_partnerledgercustomer').report_action(self, data=data, config=False)
#         return self.env['report'].get_action(self, 'account_customer_statement.report_partnerledger', data=data)#odoo11
    
    
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
