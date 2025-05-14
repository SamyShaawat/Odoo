# -*- coding: utf-8 -*-
from calendar import month
from dataclasses import field
from email.policy import default

from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import ValidationError, UserError, AccessError, ValidationError, RedirectWarning
import base64
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)


class InheritSaleOrderTemplate(models.Model):
    _name = 'quick.transations'

    date = fields.Date('Date', default=fields.Date.today())
    expense_type = fields.Many2one('expense.type', 'Expense Type', required=True)
    name = fields.Char('Description')
    amount = fields.Float('Amount', required=True)
    stage = fields.Selection([('draft', 'Draft'), ('post', 'Post')], default='draft')

    def post_transactions(self):
        lines = []
        tot_amount = 0
        for rec in self.env['quick.transations'].browse(self._context.get('active_ids')):
            if rec.stage != 'post':
                lines.append((0, 0, {
                    'account_id': rec.expense_type.account_id.id,
                    'name': rec.expense_type.expense_name,
                    'debit': rec.amount,
                }))
                rec.stage = 'post'
                tot_amount += rec.amount
        if lines:
            lines.append((0, 0, {
                'name': 'Quick Transactions' + str(fields.Date.today()),
                'credit': tot_amount,
                'account_id': 100,
            }))
            id = self.env['account.move'].create({
                'name': '/',
                'journal_id': 21,
                'date': fields.Date.today(),
                'line_ids': lines
            })
            return {
                'type': 'ir.actions.act_window',
                'name': _('Journal Entry'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'target': 'current',
                'res_id': id.id,
            }
        else:
            raise ValidationError(
                _("You Can't Post Transactions already Posted "))


class ExpenseType(models.Model):
    _name = 'expense.type'
    _rec_name = 'expense_name'

    expense_name = fields.Char('Expense Type', required=True)
    account_id = fields.Many2one('account.account', 'Account', required=True)
