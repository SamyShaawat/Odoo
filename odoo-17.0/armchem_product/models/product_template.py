# -*- coding: utf-8 -*-

import logging
import re

from odoo import api, fields, models, tools, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _compute_inch_uom_name(self):
        uom = self.env.ref('uom.product_uom_inch')
        if uom:
            self.inch_uom_name = uom.name
        else:
            self.inch_uom_name = self._get_length_uom_name_from_ir_config_parameter()

    zone2_price = fields.Float('Zone2 Price', default=0, help="Zone2Price (Freight included Prices)")
    length = fields.Float('Length', digits='Stock Length', default=0)
    inch_uom_name = fields.Char(string='Weight unit of measure label', compute='_compute_inch_uom_name')
    width = fields.Float('Width', digits='Stock Width', default=0)
    high = fields.Float('High', digits='Stock High', default=0)
