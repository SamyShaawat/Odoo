# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    full_name = fields.Char(related='employee_id.full_name')
    full_name_ar = fields.Char(related='employee_id.full_name_ar')
    join_date = fields.Date(related='employee_id.join_date')
    real_employee = fields.Boolean('Real Employee', related='employee_id.real_employee',default=True)
    employee_no = fields.Char(string="Employee number", related='employee_id.employee_no')
    service_years = fields.Integer(string="Years of Service", related='employee_id.service_years')
    service_months = fields.Integer(string="Months of Service", related='employee_id.service_months')
    service_days = fields.Integer(string="Days of Service", related='employee_id.service_days')
    family_ids = fields.One2many('hr.employee.family', 'employee_id')
    gosi_no = fields.Char('Gosi', related='employee_id.gosi_no')
    medical_insurance_no = fields.Char('Medical Insurance Membership', related='employee_id.medical_insurance_no')
    age = fields.Integer(string="Age", related='employee_id.age')
    passport_issue_date = fields.Date(related='employee_id.passport_issue_date')
    passport_expiration_date = fields.Date(related='employee_id.passport_expiration_date')
    passport_issuing_place = fields.Char(related='employee_id.passport_issuing_place')
    id_issue_date = fields.Date(related='employee_id.id_issue_date')
    id_expiration_date = fields.Date(related='employee_id.id_expiration_date')
    id_issuing_place = fields.Char(related='employee_id.id_issuing_place')
    occupation_name = fields.Char('Occupation name in Iqama & Gosi', related='employee_id.occupation_name')
    annual_leave_days = fields.Integer(string="Annual leave", related='employee_id.annual_leave_days')
    annual_leave_type = fields.Selection([('working', 'Working Days'), ('calendar', 'Calendar Days')],
                                 string='Annual Leve Type',
                                 required=True, default='working', related='employee_id.annual_leave_type')