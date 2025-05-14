from odoo import models, fields, api, _
from odoo.addons.resource.models.utils import HOURS_PER_DAY
from odoo.exceptions import ValidationError


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    is_lost = fields.Boolean(string="Lost Request")

    @api.constrains('state', 'holiday_status_id')
    def _check_gender(self):
        for record in self:
            if record.state not in ['draft', 'cancel', 'refuse'] and record.holiday_status_id.gender:
                if record.employee_id.gender != record.holiday_status_id.gender:
                    raise ValidationError(_('This Leave is not allowed for this gender.'))

    @api.constrains('state', 'holiday_status_id')
    def _check_marital_status(self):
        for record in self:
            if record.state not in ['draft', 'cancel', 'refuse'] and record.holiday_status_id.marital:
                if record.employee_id.marital != record.holiday_status_id.marital:
                    raise ValidationError(_('This Leave is not allowed for this marital status.'))

    @api.depends('date_from', 'date_to', 'resource_calendar_id', 'holiday_status_id.request_unit')
    def _compute_duration(self):
        for holiday in self:
            days, hours = holiday._get_duration()
            if (holiday.holiday_status_id.calc_type == 'calendar' or
                    (holiday.holiday_status_id.calc_type == 'employee_grade' and holiday.employee_id.annual_leave_type=='calendar')):
                public_holidays = holiday.employee_id._get_public_holidays(holiday.request_date_from, holiday.request_date_to)
                days = (holiday.date_to - holiday.date_from).days -len(public_holidays)+ 1
                hours = HOURS_PER_DAY * days
            holiday.number_of_hours = hours
            holiday.number_of_days = days

    @api.onchange('date_from', 'date_to', 'holiday_status_id', 'holiday_status_id.max_days_allowed', 'number_of_days')
    def _compute_max_allowed(self):
        for rec in self:
            if rec.holiday_status_id.max_days_allowed > 0:
                max_leave = rec.holiday_status_id.max_days_allowed
                if rec.number_of_days > max_leave:
                    raise ValidationError(
                        _('You are not allowed to request leave greater than %s days' % max_leave))
