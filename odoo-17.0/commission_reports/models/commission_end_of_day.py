# -*- coding: utf-8 -*-

import ast
import copy
import io
import json
import logging
import markupsafe
from collections import defaultdict
from datetime import datetime, date
from math import copysign, inf
from markupsafe import Markup

from odoo import api, models, _
from odoo.exceptions import RedirectWarning
from odoo.osv import expression
from odoo.tools import config, date_utils, get_lang
from odoo.tools.misc import formatLang, format_date
from odoo.tools.misc import xlsxwriter


class CommissionEndOfDayReport(models.TransientModel):
    _name = "commission.endof.day.report"
    _description = "Commission End of Day Report"

    def _prepare_options(self, options):
        date_to = options.get('date_to', False)
        if not date_to:
            cur_date = datetime.today().strftime('%Y-%m-%d')
            date_to = cur_date
        options.update({
            'date_to': date_to
        })
        return options

    def _get_amount(self, sale_orders):
        amount = sum(sale_orders.mapped('amount_untaxed'))
        return round(amount, 2)

    def _get_cost(self, sale_orders):
        cost = 0
        for order_line in sale_orders.mapped('order_line'):
            if order_line.product_id:
                cost += order_line.product_id.standard_price * order_line.product_uom_qty
        return round(cost, 2)

    @api.model
    def get_lines(self, options):
        options = self._prepare_options(options)
        date_to = datetime.strptime(options['date_to'], '%Y-%m-%d')
        # date_from = date(date_to.year, 1, 1)
        date_from = date_to.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        result = []
        user_domain = []
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            user_domain = [('company_id', '=', self.env.company.id)]
        else:
            user_domain = [('id', '=', self.env.user.id)]
        users = self.env['res.users'].search(user_domain, order='name')
        for user in users:
            sale_orders = self.env['sale.order'].search(
                [('user_id', '=', user.id), ('date_order', '>=', date_from),
                 ('date_order', '<=', date_to), ('state', 'in', ['sale','done'])])
            if sale_orders:
                amount = self._get_amount(sale_orders)
                cost = self._get_cost(sale_orders)
                vals = {
                    "user": user.name,
                    "date": options['date_to'],
                    "orders": len(sale_orders.ids),
                    "lines": len(sale_orders.mapped('order_line').ids),
                    "amount": amount,
                    "cost": cost,
                }
                result.append(vals)
        return result

    @api.model
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
            "commission_reports.report_commission_end_of_day_print",
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
        result['html'] = self.env.ref('commission_reports.report_commission_end_of_day')._render(rcontext)
        return result

    @api.model
    def get_html(self, options, **kwargs):
        res = self.search([('create_uid', '=', self.env.uid)], limit=1)
        if not res:
            return self.create({})._get_html(options)
        return res._get_html(options)

    @api.model
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

        headers = ['User', 'Date', 'Orders', 'Lines', 'Amount', 'Cost']

        x_offset = 0
        y_offset = len(headers) - 2
        sheet.write(x_offset, y_offset, 'Date', default_style)
        sheet.write_datetime(x_offset, y_offset + 1, datetime.strptime(options['date_to'], '%Y-%m-%d'),
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
            sheet.write_datetime(x_offset, 1, datetime.strptime(line['date'], '%Y-%m-%d'), date_default_style)
            sheet.write_number(x_offset, 2, line['orders'], default_style)
            sheet.write_number(x_offset, 3, line['lines'], default_style)
            sheet.write_number(x_offset, 4, line['amount'], default_style)
            sheet.write_number(x_offset, 5, line['cost'], default_style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
