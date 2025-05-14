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


class TaskLog(models.Model):
    _name = 'tree.log'

    date = fields.Date('Date')
    tree_done = fields.Integer('Tree Done')
    logged_date = fields.Datetime('Logged On', default=fields.Date.today(), readonly=True)
    task_id = fields.Many2one('project.task')
