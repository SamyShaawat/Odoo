# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class HrEmployeeSettlement(models.Model):
    _name = 'hr.employee.settlement'
    _description = 'HR Payroll Settlement Request'

    number = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    type = fields.Selection([('alw', 'Allowance'), ('ded', 'Deduction')], string='Type')
    settlement_id = fields.Many2one('hr.settlement.type', ondelete='restrict')
    calculation_method = fields.Selection([('fixed', 'Fixed'), ('percentage_basic', 'Percentage of Basic')],
                                          string='Calculation Method')
    percentage = fields.Float(string='Percentage')
    amount = fields.Float(string='Amount')
    duration = fields.Integer(string='Duration(months)')
    total_amount = fields.Float(string='Total Amount')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', compute="_compute_end_date")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),('cancel', 'Cancelled')],default='draft',string='State')
    notes = fields.Text()

    _rec_name = 'number'

    @api.depends('start_date', 'duration')
    def _compute_end_date(self):
        for rec in self:
            if rec.start_date and rec.duration:
                rec.end_date = rec.start_date + relativedelta(months=rec.duration)
            else:
                rec.end_date = rec.start_date



    def unlink(self):
        if any(self.filtered(lambda settlement: settlement.state not in ('draft', 'cancel'))):
            raise UserError(_('You cannot delete a request which is not draft or cancelled!'))
        return super(HrEmployeeSettlement, self).unlink()

    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        for vals in vals_list:
            vals['number'] = self.env['ir.sequence'].next_by_code(self._name)
        return super(HrEmployeeSettlement, self).create(vals_list)

    def action_confirm(self):
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    @api.onchange('percentage', 'calculation_method', 'employee_id')
    def compute_amount(self):
        amount=0.0
        for rec in self:
            contract = rec.employee_id.contract_id
            if rec.calculation_method == 'percentage_basic':
                amount = (contract.total_wage * rec.percentage)/100
        self.amount = amount
        self.total_amount = amount * rec.duration


class HrSettlement(models.Model):
    _name = 'hr.settlement.type'
    _description = 'HR Payroll Settlement'

    name = fields.Char('Name')
    salary_rule_id = fields.Many2one('hr.salary.rule')
    type = fields.Selection([('alw', 'Allowance'), ('ded', 'Deduction')], string='Type')
    code = fields.Char(related='salary_rule_id.code', string='Type')

