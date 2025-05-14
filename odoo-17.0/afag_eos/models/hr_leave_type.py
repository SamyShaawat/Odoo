# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    eos_computed = fields.Boolean('Computed in EOS')