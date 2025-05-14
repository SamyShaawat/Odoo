# -*- coding: utf-8 -*-
from calendar import month
from datetime import timedelta
from email.policy import default

from chardet import detect_all
from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import ValidationError, UserError, AccessError, ValidationError, RedirectWarning
import base64
from io import BytesIO
from datetime import datetime, time
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class InheritProjectTask(models.Model):
    _inherit = 'project.task'

    tree_log = fields.One2many('tree.log', 'task_id')
    trees = fields.Integer('Trees', related='sale_order_id.num_of_trees')
    completed_tress = fields.Float('Completed Trees', compute='get_completed_trees')
    completion = fields.Float(compute='get_completed_trees')
    quick_transactions = fields.One2many('quick.transations', 'task_id')

    @api.onchange('tree_log')
    def get_completed_trees(self):
        for rec in self:
            total = 0
            for i in rec.tree_log:
                total += i.tree_done
            rec.completed_tress = total
            if rec.trees > 0:
                rec.completion = (rec.completed_tress / rec.trees) * 100
            else:
                rec.completion = 0

