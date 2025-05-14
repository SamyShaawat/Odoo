# -*- coding: utf-8 -*-

import logging
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


from odoo.tools import float_compare, float_round

_logger = logging.getLogger(__name__)

class ProductCategory(models.Model):
    _inherit = "product.category"

    cat_commission = fields.Float('Category Commission', default=0, help="Category Commission")
    max_discount = fields.Float('Maximum Discount', default=0, help="Maximum Discount")
    price_margin = fields.Float('Price Margin', default=0, help="Price Margin")