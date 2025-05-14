# -*- coding: utf-8 -*-

import ast
import copy
import io
import json
import logging
import markupsafe
from collections import defaultdict
from datetime import datetime
from math import copysign, inf
from markupsafe import Markup

from odoo import api, models, _
from odoo.exceptions import RedirectWarning
from odoo.osv import expression
from odoo.tools import config, date_utils, get_lang
from odoo.tools.misc import formatLang, format_date
from odoo.tools.misc import xlsxwriter


class CommissionTotalReport(models.TransientModel):
    _name = "commission.total.report"
    _description = "Commission History Report"

    def _prepare_options(self, options):
        filter_by = options.get('filter_by', 'x_studio_date_of_full_payment')
        date_from = options.get('date_from', False)
        date_to = options.get('date_to', False)
        if not date_from or not date_to:
            cur_date = datetime.today().strftime('%Y-%m-%d')
            date_from = cur_date
            date_to = cur_date
        options.update({
            'filter_by': filter_by,
            'date_from': date_from,
            'date_to': date_to
        })
        return options

    def _get_list_price(self, account_move_lines):
        list_price = 0
        for account_move_line in account_move_lines:
            if account_move_line.product_id:
                list_price += account_move_line.product_id.list_price * account_move_line.quantity
        return round(list_price, 2)

    def _get_discount_amount(self, sale_order_lines):
        discount_amount = sum(sale_order_lines.mapped('discount_amount'))
        return round(discount_amount, 2)

    def _get_sold_price(self, account_moves):
        amount_untaxed = sum(account_moves.mapped('amount_untaxed_signed'))
        return round(amount_untaxed, 2)

    def _get_loaded_cost(self, account_move_lines):
        loaded_cost = 0
        for account_move_line in account_move_lines:
            loaded_cost += account_move_line.total_cost_price * 1.07
        return round(loaded_cost, 2)

    def _get_commission_earned(self, sale_order_lines):
        commission_earned = sum(sale_order_lines.mapped('commission_earned'))
        return round(commission_earned, 2)

    def _get_profit_price(self, sale_order_lines, sold_price, loaded_cost):
        profit_price = sold_price - loaded_cost
        return round(profit_price, 2)

    def _get_profit_percentage(self, sale_order_lines, sold_price, profit_price):
        try:
            profit_percentage = profit_price / sold_price
        except Exception as e:
            profit_percentage = 0
        return round(profit_percentage, 2)

    @api.model
    def get_lines(self, options):
        options = self._prepare_options(options)
        result = []
        user_domain = []
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            user_domain = [('company_id', '=', self.env.company.id)]
        else:
            user_domain = [('id', '=', self.env.user.id)]
        users = self.env['res.users'].search(user_domain, order='name')
        for user in users:
            account_moves = self.env['account.move'].search(
                [('invoice_user_id', '=', user.id), (options['filter_by'], '>=', options['date_from']),
                 (options['filter_by'], '<=', options['date_to']), ('move_type', '=', 'out_invoice'),
                 ('state', '=', 'posted')])
            account_move_lines = account_moves.mapped('invoice_line_ids')
            sale_order_lines = account_move_lines.mapped('sale_line_ids')

            list_price = self._get_list_price(account_move_lines)
            discount_amount = self._get_discount_amount(sale_order_lines)
            sold_price = self._get_sold_price(account_moves)
            loaded_cost = self._get_loaded_cost(account_move_lines)
            commission_earned = self._get_commission_earned(sale_order_lines)
            profit_price = self._get_profit_price(sale_order_lines, sold_price, loaded_cost)
            profit_percentage = self._get_profit_percentage(sale_order_lines, sold_price, profit_price)
            if sold_price:
                vals = {
                    "salesman_name": user.name,
                    "list_price": list_price,
                    "discount_amount": discount_amount,
                    "sold_price": sold_price,
                    "loaded_cost": loaded_cost,
                    "commission_earned": commission_earned,
                    "profit_price": profit_price,
                    "profit_percentage": profit_percentage,
                }
                result.append(vals)
        return result

    def get_pdf(self, options):
        result = {}
        context = dict(self.env.context)
        lines = self.with_context(context).get_lines(options)
        result['options'] = options

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
        }

        context = dict(self.env.context)
        context['options'] = options
        if not config['test_enable']:
            context['commit_assetsbundle'] = True
        if context.get('active_id') and context.get('active_model'):
            rcontext['reference'] = self.id

        body = self.env['ir.ui.view'].with_context(context)._render_template(
            "commission_reports.report_commission_total_print",
            values=dict(rcontext, lines=lines, report=self, context=context),
        )

        header = self.env['ir.actions.report']._render_template("web.internal_layout", values=rcontext)
        header = self.env['ir.actions.report']._render_template("web.minimal_layout", values=dict(rcontext, subst=True,
                                                                                                  body=Markup(
                                                                                                      header.decode())))

        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header.decode(),
            landscape=True,
            specific_paperformat_args={'data-report-margin-top': 17, 'data-report-header-spacing': 12}
        )

    def _get_html(self, options):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext['lines'] = self.with_context(context).get_lines(options)
        result['options'] = options
        result['html'] = self.env.ref('commission_reports.report_commission_total')._render(rcontext)
        return result

    @api.model
    def get_html(self, options, **kwargs):
        res = self.search([('create_uid', '=', self.env.uid)], limit=1)
        if not res:
            return self.create({})._get_html(options)
        return res._get_html(options)

    def get_xlsx(self, options, response=None):
        context = dict(self.env.context)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet('Test Worksheet')

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        headers = ['Rep. Name', 'List Price', 'Discount', 'Sold Price', 'Loaded Cost', 'Calculated Comm', 'Profit$',
                   'Profit%']

        x_offset = 0
        y_offset = len(headers) - 4
        sheet.write(x_offset, y_offset, 'Date From', default_style)
        sheet.write_datetime(x_offset, y_offset + 1, datetime.strptime(options['date_to'], '%Y-%m-%d'),
                             date_default_style)
        sheet.write(x_offset, y_offset + 2, 'Date To', default_style)
        sheet.write_datetime(x_offset, y_offset + 3, datetime.strptime(options['date_to'], '%Y-%m-%d'),
                             date_default_style)

        # Add headers.
        x_offset += 1
        y_offset = 0
        for header in headers:
            sheet.write(x_offset, y_offset, header, title_style)
            y_offset += 1

        lines = self.with_context(context).get_lines(options)
        for line in lines:
            x_offset += 1
            sheet.write(x_offset, 0, line['salesman_name'], default_style)
            sheet.write_number(x_offset, 1, line['list_price'], default_style)
            sheet.write_number(x_offset, 2, line['discount_amount'], default_style)
            sheet.write_number(x_offset, 3, line['sold_price'], default_style)
            sheet.write_number(x_offset, 4, line['loaded_cost'], default_style)
            sheet.write_number(x_offset, 5, line['commission_earned'], default_style)
            sheet.write_number(x_offset, 6, line['profit_price'], default_style)
            sheet.write_number(x_offset, 7, line['profit_percentage'], default_style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
