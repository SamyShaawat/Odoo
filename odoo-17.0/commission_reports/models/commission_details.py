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


class CommissionDetailsReport(models.TransientModel):
    _name = "commission.details.report"
    _description = "Commission Details Report"

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

    def _get_product_price_unit(self, account_move_line):
        product_price_unit = account_move_line.price_unit * account_move_line.quantity
        return round(product_price_unit, 2)

    def _get_product_list_price(self, account_move_line):
        product_list_price = account_move_line.product_id.list_price * account_move_line.quantity
        return round(product_list_price, 2)

    def _get_product_standard_price(self, account_move_line):
        product_standard_price = account_move_line.product_id.standard_price * account_move_line.quantity
        return round(product_standard_price, 2)

    @api.model
    def get_lines(self, options):
        options = self._prepare_options(options)
        result = []
        domain = []
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            domain = [('company_id', '=', self.env.company.id), (options['filter_by'], '>=', options['date_from']),
                      (options['filter_by'], '<=', options['date_to'])]
        else:
            domain = [('invoice_user_id', '=', self.env.user.id), (options['filter_by'], '>=', options['date_from']),
                      (options['filter_by'], '<=', options['date_to'])]
        account_moves = self.env['account.move'].search(domain)
        for account_move in account_moves:
            for account_move_line in account_move.invoice_line_ids:
                vals = {}
                if account_move_line.product_id:
                    vals = {
                        'salesman_name': account_move.invoice_user_id.name if account_move.invoice_user_id else account_move_line.sale_line_ids.salesman_id.name,
                        'partner_name': account_move.partner_id.name,
                        'invoice_number': account_move.name,
                        'invoice_paid_date': account_move.x_studio_date_of_full_payment.date() if account_move.x_studio_date_of_full_payment else account_move.x_studio_date_of_full_payment,
                        'invoice_date': account_move.invoice_date,
                        'zone': account_move.zone2_price,
                        'qty_delivered': account_move_line.sale_line_ids.qty_delivered,
                        'commission_percent': account_move_line.sale_line_ids.commission_percent,
                        'commission_earned': account_move_line.sale_line_ids.commission_earned,
                        'product_price_unit': self._get_product_price_unit(account_move_line),
                        'discount_amount': account_move_line.sale_line_ids.discount_amount,
                        'product_name': account_move_line.product_id.name,
                        'product_list_price': self._get_product_list_price(account_move_line),
                        'product_standard_price': self._get_product_standard_price(account_move_line),
                    }
                if account_move_line.product_id and account_move_line.product_id.categ_id:
                    vals.update({
                        'product_category_commission': account_move_line.product_id.categ_id.cat_commission,
                        'product_category': account_move_line.product_id.categ_id.name,
                    })
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
            "commission_reports.report_commission_details_print",
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
        result['html'] = self.env.ref('commission_reports.report_commission_details')._render(rcontext)
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

        headers = ['Salesman', 'Customer', 'Invoice Number', 'Invoice Paid Date', 'Invoice Date', 'Product',
                   'Zone2 Price', 'QtyShipped', 'Category Comm', 'Category', 'Calculated Comm%', 'Earned Comm',
                   'Sold Price Total', 'List Price Total', 'Discount', 'Cost Total']

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
            sheet.write(x_offset, 1, line['partner_name'], default_style)
            sheet.write(x_offset, 2, line['invoice_number'], default_style)
            if line['invoice_paid_date']:
                sheet.write_datetime(x_offset, 3, line['invoice_paid_date'], date_default_style)
            sheet.write_datetime(x_offset, 4, line['invoice_date'], date_default_style)
            sheet.write(x_offset, 5, line['product_name'], default_style)
            sheet.write(x_offset, 6, line['zone'], default_style)
            sheet.write_number(x_offset, 7, line['qty_delivered'], default_style)
            sheet.write_number(x_offset, 8, line['product_category_commission'], default_style)
            sheet.write(x_offset, 9, line['product_category'], default_style)
            sheet.write_number(x_offset, 10, line['commission_percent'], default_style)
            sheet.write_number(x_offset, 11, line['commission_earned'], default_style)
            sheet.write_number(x_offset, 12, line['product_price_unit'], default_style)
            sheet.write_number(x_offset, 13, line['product_list_price'], default_style)
            sheet.write_number(x_offset, 14, line['discount_amount'], default_style)
            sheet.write_number(x_offset, 15, line['product_standard_price'], default_style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
