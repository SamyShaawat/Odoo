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


class ProjectServiceLine(models.Model):
    _name = 'project.service.line'

    service_type = fields.Many2one('product.template', domain=[('detailed_type', '=', 'service')])
    months = fields.Many2many('months.model', string='Months')
    unit_price = fields.Float('Unit Price')
    qty = fields.Integer('Quantity')
    subtotal = fields.Float('Subtotal', compute='get_subtotal')
    sale_order_template_id = fields.Many2one('sale.order.template')
    sale_order_id = fields.Many2one('sale.order')
    created = fields.Boolean('Created', readonly=True)

    @api.onchange('unit_price', 'qty')
    def get_subtotal(self):
        for rec in self:
            rec.subtotal = rec.qty * rec.unit_price

    @api.onchange('service_type')
    def get_unit_price(self):
        for rec in self:
            rec.unit_price = rec.service_type.list_price
