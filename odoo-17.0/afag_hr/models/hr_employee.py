# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


class Employee(models.Model):
    _inherit = ["hr.employee"]

    full_name = fields.Char()
    full_name_ar = fields.Char()
    join_date = fields.Date()
    real_employee = fields.Boolean('Real Employee', default=True)
    employee_no = fields.Char(string="Employee number")
    service_years = fields.Integer(compute='_compute_service_duration', string="Years of Service")
    service_months = fields.Integer(compute='_compute_service_duration', string="Months of Service")
    service_days = fields.Integer(compute='_compute_service_duration', string="Days of Service")
    family_ids = fields.One2many('hr.employee.family', 'employee_id')
    gosi_no = fields.Char('Gosi')
    medical_insurance_no = fields.Char('Medical Insurance Membership')
    age = fields.Integer(string="Age", compute="_compute_age")
    passport_issue_date = fields.Date()
    passport_expiration_date = fields.Date()
    passport_issuing_place = fields.Char()
    id_issue_date = fields.Date()
    id_expiration_date = fields.Date()
    id_issuing_place = fields.Char()
    occupation_name = fields.Char('Occupation name in Iqama & Gosi')
    annual_leave_days = fields.Integer(string="Annual leave")
    annual_leave_type = fields.Selection([('working', 'Working Days'), ('calendar', 'Calendar Days')],
                                 string='Annual Leve Type',
                                 required=True, default='working')

    @api.depends('birthday')
    def _compute_age(self):
        for employee in self:
            if employee.birthday:
                today = date.today()
                born = employee.birthday
                employee.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            else:
                employee.age = 0


    def _compute_service_duration(self):
        for employee in self:
            if employee.join_date:
                joining_date = employee.join_date
                current_date = date.today()

                delta = relativedelta(current_date, joining_date)

                employee.service_years = delta.years
                employee.service_months = delta.months
                employee.service_days = delta.days
            else:
                employee.service_years = 0
                employee.service_months = 0
                employee.service_days = 0


class EmployeeFamily(models.Model):
    _name = "hr.employee.family"

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char()
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ])
    relation = fields.Selection([
        ('wife', 'Wife'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('father', 'Father'),
        ('mother', 'Mother'),
    ],string='Relationship')
    phone = fields.Char()

