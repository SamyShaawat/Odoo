# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection([
        ('list_price', 'Sales Price'),
        ('standard_price', 'Cost'),
        ('zone2_price', 'Zone2 Price'),
        ('pricelist', 'Other Pricelist')], "Based on",
        default='list_price', required=True,
        help='Base price for computation.\n'
             'Sales Price: The base price will be the Sales Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Zone2 Price : Freight included price.\n'
             'Other Pricelist : Computation of the base price based on another Pricelist.')
    commission_percent = fields.Float('Commission Percentage', digits='Product Price')