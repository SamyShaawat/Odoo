from odoo import models, api, fields, Command, _
from odoo.addons.web.controllers.utils import clean_action
from odoo.exceptions import UserError, RedirectWarning
from odoo.osv import expression
from odoo.tools.misc import get_lang


class AccountTaxReportHandlerInherit(models.AbstractModel):
    _inherit = 'account.tax.report.handler'



    def action_periodic_vat_entries(self, options):
        # Return action to open form view of newly created entry
        print('_______________Start1__________________')
        report = self.env.ref('account.generic_tax_report')
        moves = self.env['account.move']

        # Get all companies impacting the report.
        end_date = fields.Date.from_string(options['date']['date_to'])
        companies = self.env['res.company'].browse(report.get_report_company_ids(options))

        # Get the moves separately for companies with a lock date on the concerned period, and those without.
        tax_locked_companies = companies.filtered(lambda c: c.tax_lock_date and c.tax_lock_date >= end_date)
        locked_companies_moves = self._get_tax_closing_entries_for_closed_period(report, options, tax_locked_companies, posted_only=False)
        posted_locked_moves = locked_companies_moves.filtered(lambda x: x.state == 'posted')
        moves += posted_locked_moves

        non_tax_locked_companies = companies - tax_locked_companies
        draft_locked_moves = locked_companies_moves.filtered(lambda x: x.state == 'draft')
        draft_closing_moves = self._get_tax_closing_entries_for_closed_period(report, options, non_tax_locked_companies, posted_only=False) \
                              + draft_locked_moves
        companies_to_regenerate = non_tax_locked_companies + draft_locked_moves.company_id
        moves += self._generate_tax_closing_entries(report, options, companies=companies_to_regenerate, closing_moves=draft_closing_moves)

        # Make the action for the retrieved move and return it.
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        action = clean_action(action, env=self.env)

        if len(moves) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = moves.id
        else:
            action['domain'] = [('id', 'in', moves.ids)]
            action['context'] = dict(ast.literal_eval(action['context']))
            action['context'].pop('search_default_posted', None)
        return action

    def _generate_tax_closing_entries(self, report, options, closing_moves=None, companies=None):
        """Generates and/or updates VAT closing entries.

        This method computes the content of the tax closing in the following way:
        - Search on all tax lines in the given period, group them by tax_group (each tax group might have its own
        tax receivable/payable account).
        - Create a move line that balances each tax account and add the difference in the correct receivable/payable
        account. Also take into account amounts already paid via advance tax payment account.

        The tax closing is done so that an individual move is created per available VAT number: so, one for each
        foreign vat fiscal position (each with fiscal_position_id set to this fiscal position), and one for the domestic
        position (with fiscal_position_id = None). The moves created by this function hence depends on the content of the
        options dictionary, and what fiscal positions are accepted by it.

        :param options: the tax report options dict to use to make the closing.
        :param closing_moves: If provided, closing moves to update the content from.
                              They need to be compatible with the provided options (if they have a fiscal_position_id, for example).
        :param companies: optional params, the companies given will be used instead of taking all the companies impacting
                          the report.
        :return: The closing moves.
        """
        print('_______________Start2__________________')

        if companies is None:
            companies = self.env['res.company'].browse(report.get_report_company_ids(options))
        end_date = fields.Date.from_string(options['date']['date_to'])

        closing_moves_by_company = defaultdict(lambda: self.env['account.move'])
        if closing_moves:
            for move in closing_moves.filtered(lambda x: x.state == 'draft'):
                closing_moves_by_company[move.company_id] |= move
        else:
            closing_moves = self.env['account.move']
            for company in companies:
                include_domestic, fiscal_positions = self._get_fpos_info_for_tax_closing(company, report, options)
                company_closing_moves = company._get_and_update_tax_closing_moves(end_date, fiscal_positions=fiscal_positions, include_domestic=include_domestic)
                closing_moves_by_company[company] = company_closing_moves
                closing_moves += company_closing_moves

        for company, company_closing_moves in closing_moves_by_company.items():

            # First gather the countries for which the closing is being done
            countries = self.env['res.country']
            for move in company_closing_moves:
                if move.fiscal_position_id.foreign_vat:
                    countries |= move.fiscal_position_id.country_id
                else:
                    countries |= company.account_fiscal_country_id

            # Check the tax groups from the company for any misconfiguration in these countries
            if self.env['account.tax.group']._check_misconfigured_tax_groups(company, countries):
                self._redirect_to_misconfigured_tax_groups(company, countries)

            for move in company_closing_moves:
                # get tax entries by tax_group for the period defined in options
                move_options = {**options, 'fiscal_position': move.fiscal_position_id.id if move.fiscal_position_id else 'domestic'}
                line_ids_vals, tax_group_subtotal = self._compute_vat_closing_entry(company, move_options)

                line_ids_vals += self._add_tax_group_closing_items(tax_group_subtotal, end_date)

                if move.line_ids:
                    line_ids_vals += [Command.delete(aml.id) for aml in move.line_ids]

                move_vals = {}
                if line_ids_vals:
                    move_vals['line_ids'] = line_ids_vals

                move.write(move_vals)

        return closing_moves

    def _get_tax_closing_entries_for_closed_period(self, report, options, companies, posted_only=True):
        """ Fetch the closing entries related to the given companies for the currently selected tax report period.
        Only used when the selected period already has a tax lock date impacting it, and assuming that these periods
        all have a tax closing entry.
        :param report: The tax report for which we are getting the closing entries.
        :param options: the tax report options dict needed to get the period end date and fiscal position info.
        :param companies: a recordset of companies for which the period has already been closed.
        :return: The closing moves.
        """
        print('_______________Start3__________________')

        end_date = fields.Date.from_string(options['date']['date_to'])
        closing_moves = self.env['account.move']
        for company in companies:
            include_domestic, fiscal_positions = self._get_fpos_info_for_tax_closing(company, report, options)
            fiscal_position_ids = fiscal_positions.ids + ([False] if include_domestic else [])
            state_domain = ('state', '=', 'posted') if posted_only else ('state', '!=', 'cancel')
            closing_moves += self.env['account.move'].search([
                ('company_id', '=', company.id),
                ('fiscal_position_id', 'in', fiscal_position_ids),
                ('tax_closing_end_date', '=', end_date),
                state_domain,
            ], limit=1)

        return closing_moves

    @api.model
    def _compute_vat_closing_entry(self, company, options):
        """Compute the VAT closing entry.

        This method returns the one2many commands to balance the tax accounts for the selected period, and
        a dictionnary that will help balance the different accounts set per tax group.
        """
        print('_______________Start4__________________')

        self = self.with_company(company) # Needed to handle access to property fields correctly

        # first, for each tax group, gather the tax entries per tax and account
        self.env['account.tax'].flush_model(['name', 'tax_group_id'])
        self.env['account.tax.repartition.line'].flush_model(['use_in_tax_closing'])
        self.env['account.move.line'].flush_model(['account_id', 'debit', 'credit', 'move_id', 'tax_line_id', 'date', 'company_id', 'display_type', 'parent_state'])
        self.env['account.move'].flush_model(['state'])

        # Check whether it is multilingual, in order to get the translation from the JSON value if present
        lang = self.env.user.lang or get_lang(self.env).code
        tax_name = f"COALESCE(tax.name->>'{lang}', tax.name->>'en_US')" if \
            self.pool['account.tax'].name.translate else 'tax.name'

        sql = f"""
            SELECT "account_move_line".tax_line_id as tax_id,
                    tax.tax_group_id as tax_group_id,
                    {tax_name} as tax_name,
                    "account_move_line".account_id,
                    COALESCE(SUM("account_move_line".balance), 0) as amount
            FROM account_tax tax, account_tax_repartition_line repartition, %s
            WHERE %s
              AND tax.id = "account_move_line".tax_line_id
              AND repartition.id = "account_move_line".tax_repartition_line_id
              AND repartition.use_in_tax_closing
            GROUP BY tax.tax_group_id, "account_move_line".tax_line_id, tax.name, "account_move_line".account_id
        """

        new_options = {
            **options,
            'all_entries': False,
            'date': dict(options['date']),
        }

        period_start, period_end = company._get_tax_closing_period_boundaries(fields.Date.from_string(options['date']['date_to']))
        new_options['date']['date_from'] = fields.Date.to_string(period_start)
        new_options['date']['date_to'] = fields.Date.to_string(period_end)
        new_options['date']['period_type'] = 'custom'
        new_options['date']['filter'] = 'custom'
        report = self.env['account.report'].browse(options['report_id'])
        new_options = report.with_context(allowed_company_ids=company.ids).get_options(previous_options=new_options)
        # Force the use of the fiscal position from the original options (_get_options sets the fiscal
        # position to 'all' when the report is the generic tax report)
        new_options['fiscal_position'] = options['fiscal_position']

        tables, where_clause, where_params = self.env.ref('account.generic_tax_report')._query_get(
            new_options,
            'strict_range',
            domain=self._get_vat_closing_entry_additional_domain()
        )
        query = sql % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.dictfetchall()
        results = self._postprocess_vat_closing_entry_results(company, new_options, results)

        tax_group_ids = [r['tax_group_id'] for r in results]
        tax_groups = {}
        for tg, result in zip(self.env['account.tax.group'].browse(tax_group_ids), results):
            if tg not in tax_groups:
                tax_groups[tg] = {}
            if result.get('tax_id') not in tax_groups[tg]:
                tax_groups[tg][result.get('tax_id')] = []
            tax_groups[tg][result.get('tax_id')].append((result.get('tax_name'), result.get('account_id'), result.get('amount')))

        # then loop on previous results to
        #    * add the lines that will balance their sum per account
        #    * make the total per tax group's account triplet
        # (if 2 tax groups share the same 3 accounts, they should consolidate in the vat closing entry)
        move_vals_lines = []
        tax_group_subtotal = {}
        currency = self.env.company.currency_id
        for tg, values in tax_groups.items():
            total = 0
            # ignore line that have no property defined on tax group
            if not tg.tax_receivable_account_id or not tg.tax_payable_account_id:
                continue
            for dummy, value in values.items():
                for v in value:
                    tax_name, account_id, amt = v
                    # Line to balance
                    move_vals_lines.append((0, 0, {'name': tax_name, 'debit': abs(amt) if amt < 0 else 0, 'credit': amt if amt > 0 else 0, 'account_id': account_id}))
                    total += amt

            if not currency.is_zero(total):
                # Add total to correct group
                key = (tg.advance_tax_payment_account_id.id or False, tg.tax_receivable_account_id.id, tg.tax_payable_account_id.id)

                if tax_group_subtotal.get(key):
                    tax_group_subtotal[key] += total
                else:
                    tax_group_subtotal[key] = total

        # If the tax report is completely empty, we add two 0-valued lines, using the first in in and out
        # account id we find on the taxes.
        if len(move_vals_lines) == 0:
            rep_ln_in = self.env['account.tax.repartition.line'].search([
                *self.env['account.tax.repartition.line']._check_company_domain(company),
                ('account_id.deprecated', '=', False),
                ('repartition_type', '=', 'tax'),
                ('document_type', '=', 'invoice'),
                ('tax_id.type_tax_use', '=', 'purchase')
            ], limit=1)
            rep_ln_out = self.env['account.tax.repartition.line'].search([
                *self.env['account.tax.repartition.line']._check_company_domain(company),
                ('account_id.deprecated', '=', False),
                ('repartition_type', '=', 'tax'),
                ('document_type', '=', 'invoice'),
                ('tax_id.type_tax_use', '=', 'sale')
            ], limit=1)

            if rep_ln_out.account_id and rep_ln_in.account_id:
                move_vals_lines = [
                    Command.create({
                        'name': _('Tax Received Adjustment'),
                        'debit': 0,
                        'credit': 0.0,
                        'account_id': rep_ln_out.account_id.id
                    }),

                    Command.create({
                        'name': _('Tax Paid Adjustment'),
                        'debit': 0.0,
                        'credit': 0,
                        'account_id': rep_ln_in.account_id.id
                    })
                ]

        return move_vals_lines, tax_group_subtotal

    def _get_vat_closing_entry_additional_domain(self):
        print('_______________Start5__________________')

        return []

    def _postprocess_vat_closing_entry_results(self, company, options, results):
        # Override this to, for example, apply a rounding to the lines of the closing entry
        print('_______________Start6__________________')

        return results

    @api.model
    def _add_tax_group_closing_items(self, tax_group_subtotal, end_date):
        """Transform the parameter tax_group_subtotal dictionnary into one2many commands.

        Used to balance the tax group accounts for the creation of the vat closing entry.
        """
        print('_______________Start7__________________')

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
        sql_account = '''
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

    @api.model
    def _redirect_to_misconfigured_tax_groups(self, company, countries):
        """ Raises a RedirectWarning informing the user his tax groups are missing configuration
        for a given company, redirecting him to the tree view of account.tax.group, filtered
        accordingly to the provided countries.
        """
        print('_______________Start8__________________')

        need_config_action = {
            'type': 'ir.actions.act_window',
            'name': 'Tax groups',
            'res_model': 'account.tax.group',
            'view_mode': 'tree',
            'views': [[False, 'list']],
            'context': len(countries) == 1 and {'search_default_country_id': countries.ids or {}},
            # More than 1 id into search_default isn't supported
        }

        raise RedirectWarning(
            _('Please specify the accounts necessary for the Tax Closing Entry.'),
            need_config_action,
            _('Configure your TAX accounts - %s', company.display_name),
        )

    def _get_fpos_info_for_tax_closing(self, company, report, options):
        """ Returns the fiscal positions information to use to generate the tax closing
        for this company, with the provided options.

        :return: (include_domestic, fiscal_positions), where fiscal positions is a recordset
                 and include_domestic is a boolean telling whether or not the domestic closing
                 (i.e. the one without any fiscal position) must also be performed
        """
        print('_______________Start9_________________')

        if options['fiscal_position'] == 'domestic':
            fiscal_positions = self.env['account.fiscal.position']
        elif options['fiscal_position'] == 'all':
            fiscal_positions = self.env['account.fiscal.position'].search([
                *self.env['account.fiscal.position']._check_company_domain(company),
                ('foreign_vat', '!=', False),
            ])
        else:
            fpos_ids = [options['fiscal_position']]
            fiscal_positions = self.env['account.fiscal.position'].browse(fpos_ids)

        if options['fiscal_position'] == 'all':
            fiscal_country = company.account_fiscal_country_id
            include_domestic = not fiscal_positions \
                               or not report.country_id \
                               or fiscal_country == fiscal_positions[0].country_id
        else:
            include_domestic = options['fiscal_position'] == 'domestic'

        return include_domestic, fiscal_positions

    def _get_amls_with_archived_tags_domain(self, options):
        print('_______________Start10__________________')

        domain = [
            ('tax_tag_ids.active', '=', False),
            ('parent_state', '=', 'posted'),
            ('date', '>=', options['date']['date_from']),
        ]
        if options['date']['mode'] == 'single':
            domain.append(('date', '<=', options['date']['date_to']))
        return domain

    def action_open_amls_with_archived_tags(self, options, params=None):
        print('_______________Start11__________________')

        return {
            'name': _("Journal items with archived tax tags"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'domain': self._get_amls_with_archived_tags_domain(options),
            'context': {'active_test': False},
            'views': [(self.env.ref('account_reports.view_archived_tag_move_tree').id, 'list')],
        }

