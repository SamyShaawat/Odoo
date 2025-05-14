# -*- coding: utf-8 -*-
from logging import exception

from odoo import models, fields, SUPERUSER_ID, api, _, exceptions
from dateutil.relativedelta import relativedelta
from datetime import datetime


class HREosRequest(models.Model):
    _name = 'hr.eos.request'
    _description = 'End Of service request'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin', 'resource.mixin']

    name = fields.Char(string='Number', required=True, readonly=True, copy=False, default=_('New'))
    employee_id = fields.Many2one('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', required=True, string='Company', default=lambda self: self.env.company)
    parent_id = fields.Many2one('hr.employee', related='employee_id.parent_id',string= 'Manager')
    join_date = fields.Date(related='employee_id.join_date')
    contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id', store=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    date = fields.Date('Last Working Date')
    reason_id = fields.Many2one('hr.eos.reason', 'Reason', ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('paid', 'Paid'),
        ('done', 'Done'),
    ],default='draft',string='State', tracking=True)
    service_years = fields.Integer(compute='_compute_service_duration', string="Years of Service")
    service_months = fields.Integer(compute='_compute_service_duration', string="Months of Service")
    service_days = fields.Integer(compute='_compute_service_duration', string="Days of Service")
    eos_amount = fields.Float(compute='_calc_amount', store=True)
    unpaid_leave = fields.Float(compute='_get_unpaid_leaves', store=True, string='Unpaid Days')
    deduct_unpaid = fields.Boolean('Deduct Unpaid days')
    currency_id = fields.Many2one('res.currency', string='Company Currency',
                                  related='company_id.currency_id', readonly=True)
    total_salary = fields.Monetary(related='employee_id.contract_id.total_wage', currency_field='currency_id', store=True)
    remaining_leaves = fields.Float('Remaining Leaves', compute='_calc_remaining_leaves')
    leave_compensation = fields.Float('Leaves Compensation', compute='_calc_remaining_leaves')
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', ondelete='set null', copy=False)
    eos_structure_id = fields.Many2one('hr.payroll.structure', compute='_compute_eos_structure')
    payslip_net_amount = fields.Float(compute="compute_payslip_net_amount")
    article_77 = fields.Boolean()
    article_77_compensation = fields.Float(compute="_compute_article_77_compensation", store=True)
    notes = fields.Text()


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise exceptions.UserError('You can only delete records that are in draft state.')
        return super(HREosRequest,self).unlink()

    @api.depends('article_77')
    def _compute_article_77_compensation(self):
        result = self.total_salary * 2 if self.article_77 else 0
        self.article_77_compensation = result

    def compute_payslip_net_amount(self):
        # Get the payslip record (for example, by ID)
        payslip = self.env['hr.payslip'].browse(self.payslip_id.id)

        # Access the net amount (assuming it's stored in 'net_wage')
        net_amount = payslip.line_ids.filtered(lambda l: l.code == 'NETEOS').amount

        self.payslip_net_amount = net_amount



    def _compute_eos_structure(self):
        eos_structure_id = self.env['hr.payroll.structure'].sudo().search([('is_eos','=',True)], limit=1)
        self.eos_structure_id = eos_structure_id

    def action_draft(self):
        for rec in self:
            rec.state='draft'

    def action_confirm(self):
        for rec in self:
            rec.state='confirm'

    def action_approve(self):
        for rec in self:
            rec.state='done'

    def action_payslip(self):
        if not self.payslip_id:
            payslip = self.env['hr.payslip'].with_user(SUPERUSER_ID).create({'employee_id': self.employee_id.id,
                                                                             'name': _(
                                                                             'End Of Service of the employee %s') % self.employee_id.name,
                                                                             'contract_id': self.contract_id.id,
                                                                             'struct_id': self.eos_structure_id.id,
                                                                             'date_from': self.join_date,
                                                                             'date_to': self.date,
                                                                             'eos_id': self.id,
                                                                             })
            payslip_msg = _(
                "This payslip has been created from: <a href=# data-oe-model=hr.eos.request data-oe-id=%d>%s</a>") % (
                              self.id, self.name)
            payslip.with_user(SUPERUSER_ID).message_post(body=payslip_msg)
            payslip.compute_sheet()
            # self.write({'payslip_id': payslip.id, 'state': 'paid'})
            self.write({'payslip_id': payslip.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'name': 'Pay slip',
            'res_id': self.payslip_id.id,
            'view_mode': 'form',
        }

    def action_open_payslip(self):
        self.ensure_one()
        return {
            'name': _('Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'res_id': self.payslip_id.id,
            'view_mode': 'form'
        }

    @api.depends('employee_id')
    def _calc_remaining_leaves(self):
        for rec in self:
            rec.remaining_leaves = 0
            rec.leave_compensation = 0
            if rec.employee_id:
                leave_balance = self.env['hr.leave.balance'].sudo().search([('employee_id', '=', rec.employee_id.id)], limit=1)
                if leave_balance:
                    rec.remaining_leaves = leave_balance.remaining
                    rec.leave_compensation = (rec.employee_id.contract_id.total_wage/30)*leave_balance.remaining

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(self._name)
        return super(HREosRequest, self).create(vals_list)

    @api.depends('join_date', 'date')
    def _compute_service_duration(self):
        for rec in self:
            if rec.join_date and rec.date:
                joining_date = rec.join_date
                last_working_date = rec.date

                if rec.deduct_unpaid:
                    last_working_date = last_working_date-relativedelta(days=rec.unpaid_leave)

                delta = relativedelta(last_working_date, joining_date)

                rec.service_years = delta.years
                rec.service_months = delta.months
                rec.service_days = delta.days
            else:
                rec.service_years = 0
                rec.service_months = 0
                rec.service_days = 0

    @api.depends('reason_id', 'join_date', 'date', 'deduct_unpaid')
    def _calc_amount(self):
        for rec in self:
            salary=rec.total_salary
            result = 0
            if rec.reason_id.type == 'resignation':
                if rec.service_years < 2:
                    result = 0
                elif rec.service_years < 5:
                    result = (1.0 / 6) * salary * rec.service_years
                elif rec.service_years < 10:
                    result = ((1.0 / 3) * salary * 5) + ((2.0 / 3) * salary * (rec.service_years - 5))
                else:
                    result = (0.5 * salary * 5) + (salary * (rec.service_years - 5))
            elif rec.reason_id.type == 'end_of_contract':
                if rec.service_years <= 5:
                    result = 0.5 * salary * rec.service_years
                else:
                    result = (0.5 * salary * 5) + (salary * (rec.service_years - 5))
            else:
                result=0
            rec.eos_amount=result

    def get_portion_of_date_spanned(self, start_date, end_date):
        # Calculate the total number of days in the range
        start_date = datetime(start_date.year, start_date.month, start_date.day, 1, 1)
        end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59)
        total_days = (end_date - start_date).days + 1

        # Split the period into two years
        start_year_end = datetime(start_date.year, 12, 31)
        end_year_start = datetime(end_date.year, 1, 1)

        # Days in the first year
        if start_date.year == end_date.year:
            first_year_days = total_days
        else:
            first_year_days = (start_year_end - start_date).days + 2

        # Days in the second year
        if start_date.year == end_date.year:
            second_year_days = 0
        else:
            second_year_days = (end_date - end_year_start).days + 1

        # Ratio of days in the first and second years
        first_year_ratio = first_year_days / total_days
        second_year_ratio = second_year_days / total_days

        return {
            "first_year": start_date.year,
            "first_year_days": first_year_days,
            "first_year_ratio": first_year_ratio,
            "second_year": end_date.year,
            "second_year_days": second_year_days,
            "second_year_ratio": second_year_ratio
        }

    @api.depends('join_date', 'date', 'employee_id')
    def _get_unpaid_leaves(self):
        """ Helper to compute the unpaid leaves for the current employees
            :returns dict where the key is the employee id, and the value is the unpaid leaves
        """
        accumulated_unpaid_leave = 0
        for rec in self:
            unpaid_holiday = self.env['hr.leave.type'].sudo().search([('company_id','=', rec.company_id.id)]).filtered(lambda l:
                                                                                                                        l.work_entry_type_id.code =='LEAVE90')
            if rec.join_date and rec.date and unpaid_holiday:
                first_year = rec.join_date.year
                last_year = rec.date.year

                leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                                                      ('holiday_status_id', '=', unpaid_holiday.id)])

                for year in range(first_year, last_year + 1):
                    unpaid_leave = 0
                    for leave in leaves.filtered(
                            lambda record: record.request_date_from.year == year or record.request_date_to.year == year):
                        result = self.get_portion_of_date_spanned(leave.request_date_from, leave.request_date_to)
                        if leave.request_date_from.year == year:
                            unpaid_leave += result['first_year_days']
                        elif leave.request_date_to.year == year:
                            unpaid_leave += result['second_year_days']
                    if unpaid_leave >= 21:
                        accumulated_unpaid_leave += unpaid_leave

        self.unpaid_leave = accumulated_unpaid_leave


