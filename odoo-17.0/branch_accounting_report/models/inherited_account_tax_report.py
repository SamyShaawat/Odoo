# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api
from odoo.tools.translate import _
from odoo.tools.misc import formatLang

class AccountReportInherit(models.AbstractModel):
    _inherit = "account.report"

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountReportInherit, self)._get_options_domain(options)
        if options.get('branch_ids' , False):
            domain += [('branch_id', 'in', options.get('branch_ids'))]
        return domain

class generic_tax_report_inherit(models.AbstractModel):
    _inherit = 'account.generic.tax.report'

    filter_branch = True

    def _compute_from_amls_grids(self, options, dict_to_fill, period_number):
        """Fill dict_to_fill with the data needed to generate the report.

        Used when the report is set to group its line by tax grid.
        """
        tables, where_clause, where_params = self._query_get(options)

        branch_list = []

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

        sql = """
            SELECT
                   account_tax_report_line_tags_rel.account_tax_report_line_id,
                   SUM(COALESCE(account_move_line.balance, 0)
                       * CASE WHEN acc_tag.tax_negate THEN -1 ELSE 1 END
                       * CASE WHEN account_move_line.tax_tag_invert THEN -1 ELSE 1 END
                   ) AS balance
              FROM """ + tables + """
              JOIN account_move
                ON account_move_line.move_id = account_move.id
              JOIN account_account_tag_account_move_line_rel aml_tag
                ON aml_tag.account_move_line_id = account_move_line.id
              JOIN account_journal
                ON account_move.journal_id = account_journal.id
              JOIN account_account_tag acc_tag
                ON aml_tag.account_account_tag_id = acc_tag.id
              JOIN account_tax_report_line_tags_rel
                ON acc_tag.id = account_tax_report_line_tags_rel.account_account_tag_id
              JOIN account_tax_report_line report_line
                ON account_tax_report_line_tags_rel.account_tax_report_line_id = report_line.id
             WHERE """ + where_clause + account_query + """
               AND report_line.report_id = %s
               AND account_journal.id = account_move_line.journal_id
             GROUP BY account_tax_report_line_tags_rel.account_tax_report_line_id
        """
        params = where_params + [options['tax_report']]
        self.env.cr.execute(sql, params)
        for account_tax_report_line_id, balance in self.env.cr.fetchall():
            if account_tax_report_line_id in dict_to_fill:
                dict_to_fill[account_tax_report_line_id][0]['periods'][period_number]['balance'] = balance
                dict_to_fill[account_tax_report_line_id][0]['show'] = True