# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import json
import ast
# from dateutil import relativedelta
from datetime import datetime , date

from dateutil.relativedelta import relativedelta


class account_report_wizard(models.TransientModel):
    _name = "account.commission.report.wizard"

    _description = "Report Commission For Account Wizard"

    date_from = fields.Date("From" , requird=True ,  default= datetime.today().date().replace(month=1, day=1))
    date_to = fields.Date("To", requird=True , default= datetime.today().date().replace(month=12, day=31))
    enable_filter = fields.Boolean(string='Enable Comparison')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    partner_ids = fields.Many2many('res.partner', string="Partner", requird=True,
                                   default=lambda self: self.env['res.partner'].search([('active', '=', True)]))

    label_filter = fields.Char(string='Column Label',
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_no')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    # account_id = fields.Many2one('account.account', string="Account", required=True)
    representative_id = fields.Many2one('res.partner', string="Representative")



    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,
            # 'account_id': self.account_id.id,
            # 'account_code': self.account_id.code,
            # 'account_name': self.account_id.name,
            'partner_ids': self.partner_ids.ids,
            'representative_id' : self.representative_id.id,
            'date_start': self.date_from,
            'date_end': self.date_to,
            'representative_name': self.representative_id.name,

        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('commission_report.recap_report_commission').report_action(self, data=data)




class ReportAccountingRecap(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.commission_report.accounting_recap_repor_commission_view'

    @api.model
    def _get_report_values(self, docids, data):
        today =  datetime.today()
        # print("AQP" * 14, type(data['account_id']))
        start = data['date_start']
        end = data['date_end']
        if not start:
            start = (today - relativedelta(years=10)).strftime('%Y-%m-%d')
        if not end :
            end = (today + relativedelta(years=10)).strftime('%Y-%m-%d')
        date_start = start
        date_end = end
        # x = data['account_id']
        # code = data['account_code']
        # name = data['account_name']
        partner_ids = data['partner_ids']
        partner_id = data['representative_id']
        representative_name = data['representative_name']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)

        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        date_diff = (date_end_obj - date_start_obj).days + 1

        docs = []
        print(partner_ids)

        # line_ids = self.env['account.move.line'].search([
        #     ('parent_state', '=', 'posted'), ('account_id', '=', x)])

        # print("QQ" * 12, line_ids.partner_id)
        partner_ids_loop = self.env['res.partner'].search([('id', '=', partner_id), ('active', '=', True)]) if partner_id else self.env['res.partner'].search([('id', 'in', partner_ids), ('active', '=', True)])

        for partner in partner_ids_loop:
            print(partner)

            line_ids = self.env['account.move'].search([
                ('state', '=', 'posted'), ('representative_id', '=', partner.id), ('move_type', '=', 'out_invoice')])
            total_amount_residual = 0.0
            total_amount = 0.0
            total_ = 0.0
            if line_ids:
                amount_debit = 0.0
                amount_credit = 0.0

                

                for record in self.env['account.move'].search([
                    ('state', '=', 'posted'), ('representative_id', '=', partner.id),('move_type', '=', 'out_invoice')]):

                  if record.payment_state != 'not_paid' and record.payment_state != 'reversed'  and record.payment_state != 'invoice_legacy' :
                    print(record.invoice_payments_widget)
                    x = record.invoice_payments_widget
                    json_acceptable_string = x.replace("'", "\"")
                    d = json.loads(json_acceptable_string)
                    ref = ''
                    amount = 0.0

                    if d != False :
                       x = d['content']
                       print(x)
                       for rec in x :
                           date =  datetime.strptime(rec['date'], DATE_FORMAT)
                           date_from = datetime.strptime(data['date_start'], DATE_FORMAT).date()
                           date_to = datetime.strptime(data['date_end'], DATE_FORMAT).date()
                           print(type(date.date()))
                           if date.date() >= date_from and  date.date() <= date_to:
                              index = rec['ref'].find('(')
                              ref +=  rec['ref'][0 : index] + ' /'
                              amount += rec['amount']

                    total_amount_residual += record.amount_residual
                    total_ += record.amount_residual + amount
                    total_amount += amount


                    docs.append({
                        'name' : record.name,
                        'partner_id': record.partner_id.name,
                        'invoice_date': record.invoice_date,
                        'total': record.amount_residual + amount,
                        'amount_residual': record.amount_residual,
                        'invoice_payments_widget': record.invoice_payments_widget,
                        'amount' : amount ,
                        'ref' : ref ,
                        'representative_id' : record.representative_id.name

                    })



        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'representative_name' : representative_name ,
            'docs': docs,
            'total_amount_residual' : total_amount_residual ,
            'total_' : total_ ,
            'total_amount' : total_amount


        }
