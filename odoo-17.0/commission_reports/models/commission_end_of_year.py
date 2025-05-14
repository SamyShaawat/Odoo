# -*- coding: utf-8 -*-

import ast
import copy
import io
import json
import logging
import markupsafe
from collections import defaultdict
from datetime import datetime, date, timedelta
from math import copysign, inf
from markupsafe import Markup

from odoo import api, models, _
from odoo.exceptions import RedirectWarning
from odoo.osv import expression
from odoo.tools import config, date_utils, get_lang
from odoo.tools.misc import formatLang, format_date
from odoo.tools.misc import xlsxwriter


class CommissionEndOfYearReport(models.TransientModel):
    _name = "commission.endof.year.report"
    _description = "Commission End of Year Report"

    def _prepare_options(self, options):
        date_from = options.get('date_from', False)
        date_to = options.get('date_to', False)
        if not date_from:
            cur_date = datetime.today().strftime('%Y-%m-%d')
            date_from = cur_date
            date_to = cur_date
        options.update({
            'date_from': date_from,
            'date_to': date_to
        })
        return options

    @api.model
    def get_lines(self, options):
        options = self._prepare_options(options)

        user_domain = []
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            user_domain = [('company_id', '=', self.env.company.id)]
        else:
            user_domain = [('id', '=', self.env.user.id)]
        users = self.env['res.users'].search(user_domain, order='name')

        result = []
        for user in users:
            date_from = datetime.strptime(options['date_from'], '%Y-%m-%d')
            date_to = datetime.strptime(options['date_to'], '%Y-%m-%d')
            week_from = date_from
            month_from = date(date_from.year, date_from.month, 1)
            year_from = date(date_from.year, 1, 1)

            day_from = date_to.replace(hour=0, minute=0, second=0, microsecond=0)
            date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
            day_sale_order_ids = self.env['sale.order'].search(
                [('user_id', '=', user.id), ('date_order', '>=', day_from), ('date_order', '<=', date_to),
                 ('state', 'in', ['sale','done'])])
            day_invoice_ids = day_sale_order_ids.mapped('invoice_ids')
            day_invoice_ids = day_invoice_ids.filtered(lambda i: i.state in ['posted'])

            week_sale_order_ids = self.env['sale.order'].search(
                [('user_id', '=', user.id), ('date_order', '>=', week_from), ('date_order', '<=', date_to),
                 ('state', 'in', ['sale','done'])])
            week_invoice_ids = week_sale_order_ids.mapped('invoice_ids')
            week_invoice_ids = week_invoice_ids.filtered(lambda i: i.state in ['posted'])

            month_sale_order_ids = self.env['sale.order'].search(
                [('user_id', '=', user.id), ('date_order', '>=', month_from), ('date_order', '<=', date_to),
                 ('state', 'in', ['sale','done'])])
            month_invoice_ids = month_sale_order_ids.mapped('invoice_ids')
            month_invoice_ids = month_invoice_ids.filtered(lambda i: i.state in ['posted'])


            year_sale_order_ids = self.env['sale.order'].search(
                [('user_id', '=', user.id), ('date_order', '>=', year_from), ('date_order', '<=', date_to),
                 ('state', 'in', ['sale','done'])])
            year_invoice_ids = year_sale_order_ids.mapped('invoice_ids')
            year_invoice_ids = year_invoice_ids.filtered(lambda i: i.state in ['posted'])

            if year_sale_order_ids:
                vals = {
                    "user": user.name,
                    "orders": {
                        "day_count": len(day_sale_order_ids.ids),
                        "day_sold": round(sum(day_sale_order_ids.mapped('amount_untaxed')), 2),
                        "week_count": len(week_sale_order_ids.ids),
                        "week_sold": round(sum(week_sale_order_ids.mapped('amount_untaxed')), 2),
                        "month_count": len(month_sale_order_ids.ids),
                        "month_sold": round(sum(month_sale_order_ids.mapped('amount_untaxed')), 2),
                        "year_count": len(year_sale_order_ids.ids),
                        "year_sold": round(sum(year_sale_order_ids.mapped('amount_untaxed')), 2),
                    },
                    "invoices": {
                        "day_count": len(day_invoice_ids.ids),
                        "day_sold": round(sum(day_invoice_ids.mapped('amount_untaxed_signed')), 2),
                        "week_count": len(week_invoice_ids.ids),
                        "week_sold": round(sum(week_invoice_ids.mapped('amount_untaxed_signed')), 2),
                        "month_count": len(month_invoice_ids.ids),
                        "month_sold": round(sum(month_invoice_ids.mapped('amount_untaxed_signed')), 2),
                        "year_count": len(year_invoice_ids.ids),
                        "year_sold": round(sum(year_invoice_ids.mapped('amount_untaxed_signed')), 2),
                    },
                    "goals": {
                        "day_count": 0,
                        "day_sold": 0,
                        "week_count": 0,
                        "week_sold": 0,
                        "month_count": 0,
                        "month_sold": 0,
                        "year_count": 0,
                        "year_sold": 0,
                    },
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
            "commission_reports.report_commission_end_of_year_print",
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
            specific_paperformat_args=None,
            set_viewport_size=False
        )

    def _get_html(self, options):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext['lines'] = self.with_context(context).get_lines(options)
        result['options'] = options
        result['html'] = self.env.ref('commission_reports.report_commission_end_of_year')._render(rcontext)
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

        headers = ['Name', '', 'DayCount', 'DaySold', 'WeekCount', 'WeekSold', 'MonthCount', 'MonthSold', 'YearCount',
                   'YearSold']

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
            sheet.write(x_offset, 0, line['user'], default_style)

            # Orders
            sheet.write(x_offset, 1, 'Orders', default_style)
            sheet.write_number(x_offset, 2, line['orders']['day_count'], default_style)
            sheet.write_number(x_offset, 3, line['orders']['day_sold'], default_style)
            sheet.write_number(x_offset, 4, line['orders']['week_count'], default_style)
            sheet.write_number(x_offset, 5, line['orders']['week_sold'], default_style)
            sheet.write_number(x_offset, 6, line['orders']['month_count'], default_style)
            sheet.write_number(x_offset, 7, line['orders']['month_sold'], default_style)
            sheet.write_number(x_offset, 8, line['orders']['year_count'], default_style)
            sheet.write_number(x_offset, 9, line['orders']['year_sold'], default_style)

            # Invoices
            x_offset += 1
            sheet.write(x_offset, 1, 'Inv', default_style)
            sheet.write_number(x_offset, 2, line['invoices']['day_count'], default_style)
            sheet.write_number(x_offset, 3, line['invoices']['day_sold'], default_style)
            sheet.write_number(x_offset, 4, line['invoices']['week_count'], default_style)
            sheet.write_number(x_offset, 5, line['invoices']['week_sold'], default_style)
            sheet.write_number(x_offset, 6, line['invoices']['month_count'], default_style)
            sheet.write_number(x_offset, 7, line['invoices']['month_sold'], default_style)
            sheet.write_number(x_offset, 8, line['invoices']['year_count'], default_style)
            sheet.write_number(x_offset, 9, line['invoices']['year_sold'], default_style)

            # Goals
            x_offset += 1
            sheet.write(x_offset, 1, 'Goals', default_style)
            sheet.write_number(x_offset, 2, line['goals']['day_count'], default_style)
            sheet.write_number(x_offset, 3, line['goals']['day_sold'], default_style)
            sheet.write_number(x_offset, 4, line['goals']['week_count'], default_style)
            sheet.write_number(x_offset, 5, line['goals']['week_sold'], default_style)
            sheet.write_number(x_offset, 6, line['goals']['month_count'], default_style)
            sheet.write_number(x_offset, 7, line['goals']['month_sold'], default_style)
            sheet.write_number(x_offset, 8, line['goals']['year_count'], default_style)
            sheet.write_number(x_offset, 9, line['goals']['year_sold'], default_style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
