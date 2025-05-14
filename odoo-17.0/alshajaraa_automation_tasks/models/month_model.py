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


class MothsModel(models.Model):
    _name = 'months.model'
    _rec_name = 'name'

    name = fields.Char('Month Name')
