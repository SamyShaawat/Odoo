from odoo import models, api, fields, Command, _
from odoo.addons.web.controllers.utils import clean_action
from odoo.exceptions import UserError, RedirectWarning
from odoo.osv import expression
from odoo.tools.misc import get_lang


class AccountTaxReportHandlerInherit(models.AbstractModel):
    _inherit = 'account.tax.report.handler'

    @api.model
    def _add_tax_group_closing_items(self, tax_group_subtotal, end_date):
        """Transform the parameter tax_group_subtotal dictionnary into one2many commands.

        Used to balance the tax group accounts for the creation of the vat closing entry.
        """

        def _add_line(account, name, company_currency):
            self.env.cr.execute(sql_account, (account, end_date))
            result = self.env.cr.dictfetchone()
            advance_balance = result.get('balance') or 0
            # Deduct/Add advance payment
            if not company_currency.is_zero(advance_balance):
                line_ids_vals.append((0, 0, {
                    'name': name,
                    'debit': abs(advance_balance) if advance_balance < 0 else 0,
                    'credit': abs(advance_balance) if advance_balance > 0 else 0,
                    'account_id': account
                }))
            return advance_balance

        currency = self.env.company.currency_id
        branch = self.env.user.branch_id.id
        sql_account = f'''
               SELECT SUM(aml.balance) AS balance
               FROM account_move_line aml
               LEFT JOIN account_move move ON move.id = aml.move_id
               WHERE aml.account_id = %s
                 AND aml.date <= %s
                 AND move.state = 'posted'
                     
           '''
        line_ids_vals = []
        # keep track of already balanced account, as one can be used in several tax group
        account_already_balanced = []
        for key, value in tax_group_subtotal.items():
            total = value
            # Search if any advance payment done for that configuration
            if key[0] and key[0] not in account_already_balanced:
                total += _add_line(key[0], _('Balance tax advance payment account'), currency)
                account_already_balanced.append(key[0])
            if key[1] and key[1] not in account_already_balanced:
                total += _add_line(key[1], _('Balance tax current account (receivable)'), currency)
                account_already_balanced.append(key[1])
            if key[2] and key[2] not in account_already_balanced:
                total += _add_line(key[2], _('Balance tax current account (payable)'), currency)
                account_already_balanced.append(key[2])
            # Balance on the receivable/payable tax account
            if not currency.is_zero(total):
                line_ids_vals.append(Command.create({
                    'name': _('Payable tax amount') if total < 0 else _('Receivable tax amount'),
                    'debit': total if total > 0 else 0,
                    'credit': abs(total) if total < 0 else 0,
                    'account_id': key[2] if total < 0 else key[1]
                }))
        return line_ids_vals
