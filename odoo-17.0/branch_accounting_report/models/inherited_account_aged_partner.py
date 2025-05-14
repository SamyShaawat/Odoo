# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain


class AccountMove(models.Model):
    _inherit = 'account.move'

    branch_name = fields.Char(string='Branch Name', related='branch_id.name', store=True, index=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    branch_name = fields.Char(string='Branch Name', related='branch_id.name', store=True, index=True)


class AccountAgedPartner(models.AbstractModel):
    _inherit = 'account.aged.partner'

    filter_branch = True

    branch_id = fields.Many2one('res.branch')
    branch_name = fields.Char(group_operator='max')

    @api.model
    def _get_column_details(self, options):
        columns = [
            self._header_column(),
            self._field_column('report_date'),
            self._field_column('account_name', name=_("Account"), ellipsis=True),
            # self._field_column('branch_name', name=_("Branch")),
            # self._field_column('expected_pay_date'),
            self._field_column('period0', name=_("As of: %s", format_date(self.env, options['date']['date_to']))),
            self._field_column('period1', sortable=True),
            self._field_column('period2', sortable=True),
            self._field_column('period3', sortable=True),
            self._field_column('period4', sortable=True),
            self._field_column('period5', sortable=True),
            self._custom_column(  # Avoid doing twice the sub-select in the view
                name=_('Total'),
                classes=['text-left'],
                formatter=self.format_value,
                getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                sortable=True,
            ),
        ]

        # if self.user_has_groups('base.group_multi_currency'):
        #     columns[2:2] = [
        #         self._field_column('amount_currency'),
        #         self._field_column('currency_id'),
        #     ]
        return columns

    @api.model
    def _get_sql(self):
        options = self.env.context['report_options']
        branch_list = []

        options = self.env.context['report_options']
        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')

        account_query = ''
        if branch_list:

            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND account_move_line.branch_id = %s """ % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND account_move_line.branch_id in %s """ % (str(tuple(branches)))

            query = ("""
                SELECT
                    {move_line_fields},
                    account_move_line.amount_currency as amount_currency,
                    account_move_line.partner_id AS partner_id,
                    partner.name AS partner_name,
                    COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                    COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                    account_move_line.payment_id AS payment_id,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                    account_move_line.expected_pay_date AS expected_pay_date,
                    move.move_type AS move_type,
                    move.name AS move_name,
                    move.branch_name AS branch_name,
                    move.branch_id AS branch_id,
                    move.ref AS move_ref,
                    account.code || ' ' || account.name AS account_name,
                    account.code AS account_code,""" + ','.join([("""
                    CASE WHEN period_table.period_index = {i}
                    THEN %(sign)s * ROUND((
                        account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                    ) * currency_table.rate, currency_table.precision)
                    ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                FROM account_move_line
                JOIN account_move move ON account_move_line.move_id = move.id
                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_account account ON account.id = account_move_line.account_id
                JOIN res_partner partner ON partner.id = account_move_line.partner_id
                JOIN res_branch branch ON branch.id = account_move_line.branch_id
                LEFT JOIN ir_property trust_property ON (
                    trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                    AND trust_property.name = 'trust'
                    AND trust_property.company_id = account_move_line.company_id
                )
                JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                LEFT JOIN LATERAL (
                    SELECT part.amount, part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date)s
                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                JOIN {period_table} ON (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )
                WHERE account.internal_type = %(account_type)s
                """ + account_query + """
                AND account.exclude_from_aged_reports IS NOT TRUE
                GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                         period_table.period_index, currency_table.rate, currency_table.precision
                HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
        else:
            query = ("""
            SELECT
                {move_line_fields},
                account_move_line.amount_currency as amount_currency,
                account_move_line.partner_id AS partner_id,
                partner.name AS partner_name,
                COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                account_move_line.payment_id AS payment_id,
                COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                account_move_line.expected_pay_date AS expected_pay_date,
                move.move_type AS move_type,
                move.name AS move_name,
                move.ref AS move_ref,
                move.branch_name AS branch_name,
                move.branch_id AS branch_id,
                account.code || ' ' || account.name AS account_name,
                account.code AS account_code,""" + ','.join([("""
                CASE WHEN period_table.period_index = {i}
                THEN %(sign)s * ROUND((
                    account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                ) * currency_table.rate, currency_table.precision)
                ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
            FROM account_move_line
            JOIN account_move move ON account_move_line.move_id = move.id
            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            JOIN res_partner partner ON partner.id = account_move_line.partner_id
            JOIN res_branch branch ON branch.id = account_move_line.branch_id
            LEFT JOIN ir_property trust_property ON (
                trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                AND trust_property.name = 'trust'
                AND trust_property.company_id = account_move_line.company_id
            )
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_debit ON part_debit.debit_move_id = account_move_line.id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_credit ON part_credit.credit_move_id = account_move_line.id
            JOIN {period_table} ON (
                period_table.date_start IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
            )
            AND (
                period_table.date_stop IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
            )
            WHERE account.internal_type = %(account_type)s
            AND account.exclude_from_aged_reports IS NOT TRUE
            GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                     period_table.period_index, currency_table.rate, currency_table.precision
            HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
            

# class ReportAccountAgedReceivable(models.Model):
#     _inherit = "account.aged.receivable"


#     branch_id = fields.Many2one('res.branch')
#     branch_name = fields.Char(group_operator='max')

# class ReportAccountAgedPayable(models.Model):
#     _inherit = "account.aged.payable"

#     branch_id = fields.Many2one('res.branch')
#     branch_name = fields.Char(group_operator='max')