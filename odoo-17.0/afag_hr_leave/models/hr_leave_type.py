# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    calc_type = fields.Selection([('working', 'Working Days'), ('calendar', 'Calendar Days'), ('employee_grade', 'Employee Grade Type')], string='Calculation Type',
                                 required=True, default='working')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    is_annual = fields.Boolean('Annual Leave')
    marital = fields.Selection([('single', 'Single'),
                                ('married', 'Married'),
                                ('cohabitant', 'Cohabitant'),
                                ('widower', 'Widower'),
                                ('divorced', 'Divorced'),
                                ], string='Marital Status')
    max_days_allowed = fields.Float(string="Max Days Allowed")

