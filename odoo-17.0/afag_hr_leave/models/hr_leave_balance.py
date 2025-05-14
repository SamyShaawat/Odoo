from odoo import models, fields


class HrLeaveBalance(models.Model):
    _name = "hr.leave.balance"

    employee_id = fields.Many2one('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', required=True, string='Company', default=lambda self: self.env.company)
    leave_type = fields.Many2one('hr.leave.type', 'Leave Type', domain="[('is_annual', '=', True)]")
    balance = fields.Float('Balance', compute='_compute_total_balance')
    taken = fields.Float('Taken', compute='_compute_total_balance')
    lost = fields.Float('Lost', compute='_compute_total_balance')
    remaining = fields.Float('Remaining', compute='_compute_total_balance')
    leave_compensation = fields.Float('Compensation', compute='_compute_total_balance')
    _rec_name = 'employee_id'

    def _compute_total_balance(self):
        for rec in self:
            balance = 0
            taken = 0
            lost  = 0
            leave_compensation = 0
            if rec.employee_id and rec.leave_type:
                allocation = self.env['hr.leave.allocation'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type.id), ('state', '=', 'validate')])
                taken_leaves = self.env['hr.leave'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type.id),
                     ('state', '=', 'validate'), ('is_lost','=',False)])
                lost_leaves = self.env['hr.leave'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type.id),
                     ('state', '=', 'validate'), ('is_lost','=',True)])

                for line in  allocation:
                    balance += line.number_of_days_display

                for line in taken_leaves:
                    taken += line.number_of_days

                for line in lost_leaves:
                    lost += line.number_of_days

            rec.balance = balance
            rec.taken = taken
            rec.lost = lost
            rec.remaining = balance - taken - lost

            contract = rec.employee_id.contract_id
            if contract:
                basic = contract.wage
                housing = contract.l10n_sa_housing_allowance
                transportation = contract.l10n_sa_transportation_allowance

                leave_compensation = ((basic + housing + transportation) / 30) * rec.remaining

            rec.leave_compensation = leave_compensation


    def _set_leave_balance(self):
        for rec in self.env['hr.employee'].search([('real_employee', '=', 'True')]).filtered(lambda x:x.real_employee == True):
            annual_leave = self.env['hr.leave.type'].sudo().search([('is_annual', '=', True),('company_id','=',rec.company_id.id)], limit=1)

            previous_balance = self.env['hr.leave.balance'].search([('employee_id', '=', rec.id),
                                                                    ('leave_type', '=', annual_leave.id)])

            if not previous_balance:
                self.env['hr.leave.balance'].create({
                    'employee_id': rec.id,
                    'company_id': rec.company_id.id,
                    'leave_type': annual_leave.id,
                })
