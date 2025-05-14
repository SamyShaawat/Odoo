from email.policy import default

from chardet import detect_all
from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import ValidationError, UserError, AccessError, ValidationError, RedirectWarning
import base64
from io import BytesIO
from datetime import datetime, time, timedelta
import logging
from dateutil.relativedelta import relativedelta
from collections import defaultdict

_logger = logging.getLogger(__name__)


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    project_start_date = fields.Date('Start Date')
    project_end_date = fields.Date('End Date')
    num_of_trees = fields.Integer('Number of Trees')
    project_line_table = fields.One2many('project.service.line', 'sale_order_id')
    quick_transactions = fields.One2many('quick.transations', 'sale_order_id', compute='get_quick_transactions')
    total_expense = fields.Float(compute='get_quick_transactions')
    check_number_trees = fields.Boolean(compute='get_check_trees')
    manloper_table = fields.One2many('lapor.specialty.table', 'sale_order_id')
    total_manpower = fields.Integer(compute='get_total_manpower', string='Manpower')

    def get_quick_transactions(self):
        for rec in self:
            ids = []
            transactions = self.env['project.task'].search([('sale_order_id', '=', rec.id)])
            if transactions:
                for i in transactions:
                    for j in i.quick_transactions:
                        ids.append(j.id)
                if ids:
                    rec.quick_transactions = [(6, 0, ids)]
                    rec.total_expense = sum(rec.quick_transactions.mapped('amount'))

                else:
                    rec.quick_transactions = [(5, 0, 0)]
                    rec.total_expense = 0
            else:
                rec.quick_transactions = [(5, 0, 0)]
                rec.total_expense = 0

    def get_check_trees(self):
        for rec in self:
            if rec.num_of_trees > 0:
                rec.check_number_trees = True
            else:
                rec.check_number_trees = False

    def get_total_manpower(self):
        for rec in self:
            if rec.manloper_table:
                rec.total_manpower = sum(rec.manloper_table.mapped('count'))
            else:
                rec.total_manpower = 0


class InheritQuickTransactions(models.Model):
    _inherit = 'quick.transations'

    sale_order_id = fields.Many2one('sale.order')
    task_id = fields.Many2one('project.task')


class Manlapor(models.Model):
    _name = 'lapor.specialty'

    name = fields.Char('Description')


class ManlaporTable(models.Model):
    _name = 'lapor.specialty.table'

    manloper = fields.Many2one('lapor.specialty', string='Specialty')
    count = fields.Integer('Count')
    sale_order_id = fields.Many2one('sale.order')
