# -- coding: utf-8 --

from odoo import api, fields, models, SUPERUSER_ID, _, exceptions
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_round, date_utils, convert_file, html2plaintext
from odoo.tools.float_utils import float_compare
import math
from datetime import datetime


def relativeDelta(enddate, startdate):
    if not startdate or not enddate:
        return relativedelta()
    startdate = fields.Datetime.from_string(startdate)
    enddate = fields.Datetime.from_string(enddate) + relativedelta(days=1)
    return relativedelta(enddate, startdate)


def delta_desc(delta):
    res = []
    if delta.years:
        res.append(_('%s Years' % delta.years))
    if delta.months:
        res.append(_('%s Months' % delta.months))
    if delta.days:
        res.append(_('%s Days' % delta.days))
    return ', '.join(res)


class EndOfService(models.Model):
    _name = 'hr.end_of_service'
    _description = 'End of Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    @api.constrains('date', 'employee_id')
    def _check_validity(self):
        for eos in self:
            last_eos_request = self.env['hr.end_of_service'].search([
                ('employee_id', '=', eos.employee_id.id),
                ('date', '<=', eos.date),
                ('id', '!=', eos.id),
            ], order='date desc', limit=1)
            if last_eos_request:
                raise exceptions.ValidationError(
                    _('Cannot create new end of service request for %(empl_name)s, the employee has already a request.') % {
                        'empl_name': eos.employee_id.name
                    })

    @api.depends('employee_id', 'date')
    def _compute_contract_id(self):
        for rec in self:
            date = rec.date or fields.Date.today()
            if not rec.employee_id:
                rec.contract_id = False
                continue
            # Add a default contract if not already defined or invalid
            if rec.contract_id and rec.employee_id == rec.contract_id.employee_id:
                continue
            contracts = rec.employee_id._get_contracts(date, fields.Date.today())
            rec.contract_id = contracts[0] if contracts else False

    @api.depends('company_id')
    def _compute_active_employee_ids(self):
        for rec in self:
            company_id = rec.company_id.id or self.env.company.id
            contract_ids = self.env['hr.contract'].search([
                ('state', '=', 'open'),
                ('company_id', '=', company_id)])
            rec.active_employee_ids = contract_ids.mapped('employee_id').ids

    def _get_default_salary_structure(self):
        return self.env['hr.payroll.structure'].search([('is_end_of_service', '=', True)], limit=1)

    @api.depends('employee_id', 'contract_id')
    def _get_default_eos_rule(self):
        for rec in self:
            rule_id = self.env['hr.salary.rule'].search(
                [('struct_id', '=', rec.emp_struct_id.id), ('code', '=', 'CONTOTAL')],
                limit=1)
            rec.salary_rule_id = rule_id.id
            rec.leave_rule_id = rule_id.id

    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default=_('New'))
    active_employee_ids = fields.Many2many('hr.employee', compute='_compute_active_employee_ids')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  readonly=True, states={'draft': [('readonly', False)]},
                                  domain="[('id', 'in', active_employee_ids)]")
    contract_id = fields.Many2one(
        'hr.contract', string='Contract', domain="[('company_id', '=', company_id)]",
        compute='_compute_contract_id', required=True, store=True, readonly=True,
        states={'draft': [('readonly', False)]})
    date = fields.Date('End of Service Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_from = fields.Date(default=lambda self: fields.Date.today() + relativedelta(day=1))
    date_to = fields.Date(compute="_compute_payslip_dates")
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True)
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', readonly=True)
    reason_id = fields.Many2one('hr.end_of_service.reason', string='End of Service Reason', required=True,
                                readonly=True, states={'draft': [('readonly', False)]})
    reason_type = fields.Selection(related='reason_id.reason_type')
    termination_reason_id = fields.Many2one('hr.end_of_service.termination_reason', string='Termination Reason',
                                            readonly=True, states={'draft': [('readonly', False)]})
    eos_structure_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',
                                       default=_get_default_salary_structure,
                                       domain="[('is_end_of_service', '=', True)]", required=True, readonly=True,
                                       states={'draft': [('readonly', False)]})
    emp_struct_id = fields.Many2one(related='contract_id.structure_id')
    salary_rule_id = fields.Many2one('hr.salary.rule', string='End Of Service Rule', store=True,
                                     compute=_get_default_eos_rule)
    leave_rule_id = fields.Many2one('hr.salary.rule', string='Leave Rule', store=True,
                                    compute=_get_default_eos_rule)
    company_id = fields.Many2one('res.company', required=True, string='Company', default=lambda self: self.env.company,
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Company Currency',
                                  related='company_id.currency_id', readonly=True)
    compute_by = fields.Selection([
        ('by_years', 'By Years'),
        ('by_years_months', 'By Years And Months'),
        ('by_years_months_days', 'By Years And Months And Days'),
    ], string='Compute By', default='by_years_months_days', required=True, readonly=True)
    comments = fields.Text()
    date_of_join = fields.Date('Date of Join', related='employee_id.date_of_join', readonly=True)
    service_year = fields.Float('Total Service Years', compute='_calc_service_year', store=True)
    service_month = fields.Float('Total Service Months', compute='_calc_service_year', store=True)
    org_service_desc = fields.Char('Original Years of Service', compute='_calc_org_service_year', store=True)
    service_desc = fields.Char('Years of Service', compute='_calc_service_year', store=True)
    years_of_service = fields.Float('Years of Service', compute='_calc_service_year', store=True)
    days_of_service = fields.Float(string='Days of Service', compute='_calc_service_year', store=True)
    months_of_service = fields.Float(string='Month of Service', compute='_calc_service_year', store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', ondelete='set null', copy=False)
    annual_leave_type = fields.Selection(
        string='Annual Leave Type',
        selection=[
            ('working_days', 'Working Days'),
            ('calendar_days', 'Calendar Days')
        ],
        default='working_days', readonly=True, states={'draft': [('readonly', False)]}, tracking=True, copy=False)
    remaining_leaves = fields.Float('Remaining Leave Days', compute='_calc_remaining_leaves')
    unpaid_leave = fields.Float('Unpaid Leaves', compute='_get_unpaid_leaves')
    deduct_unpaid_leave = fields.Boolean('Deduct Unpaid Leaves')
    leave_compensation = fields.Monetary('Leaves Compensation', compute='_calc_remaining_leaves')
    total_salary = fields.Monetary(related='contract_id.total_amount')
    end_of_service_compensation = fields.Monetary('End Of Service Compensation',
                                                  compute='_calc_end_of_service_compensation', store=True)
    before_5years_compensation = fields.Monetary('Before 5 years Compensation',
                                                 compute='_calc_end_of_service_compensation', store=True)
    after_5years_compensation = fields.Monetary('After 5 years Compensation',
                                                compute='_calc_end_of_service_compensation', store=True)
    amount = fields.Monetary(compute='_calc_amount')
    article_77_compensation = fields.Monetary('Article 77 Compensation', compute='_calc_article_77_compensation')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'), ('refuse', 'Refused'),
         ('cancel', 'Cancelled'), ('paid', 'Closed')], default='draft', tracking=True)

    @api.depends('date_from')
    def _compute_payslip_dates(self):
        for rec in self:
            rec.date_to = rec.date_from + relativedelta(day=31)

    def action_confirm(self):
        self.state = 'confirm'

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'refuse'

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        if self.payslip_id.move_id:
            raise UserError(_('You cannot cancel a record which its payslip is posted'))
        else:
            self.payslip_id.sudo().action_payslip_cancel()
            self.payslip_id.sudo().unlink()
            self.state = 'cancel'

    def _get_base_local_dict(self):
        return {
            'float_round': float_round,
            'float_compare': float_compare,
            'relativedelta': relativedelta,
            'ceil': math.ceil
        }

    def _get_localdict(self):
        worked_days_dict = {}
        inputs_dict = {}
        employee = self.employee_id
        contract = self.contract_id
        localdict = {
            **self._get_base_local_dict(),
            **{
                'categories': BrowsableObject(employee.id, {}, self.env),
                'rules': BrowsableObject(employee.id, {}, self.env),
                'payslip': Payslips(employee.id, self, self.env),
                'worked_days': WorkedDays(employee.id, worked_days_dict, self.env),
                'inputs': InputLine(employee.id, inputs_dict, self.env),
                'employee': employee,
                'contract': contract,
                'result_rules': ResultRules(employee.id, {}, self.env)
            }
        }
        return localdict

    def compute_salary_rules(self, rule_ids):
        localdict = self._get_localdict()
        rules_dict = localdict['rules'].dict
        result_rules_dict = localdict['result_rules'].dict
        result = {}
        for rule in sorted(rule_ids, key=lambda x: x.sequence):
            localdict.update({
                'result': None,
                'result_qty': 1.0,
                'result_rate': 100,
                'result_name': False
            })
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)
                # check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                # set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                # Retrieve the line name in the employee's lang
                employee_lang = self.employee_id.sudo().address_home_id.lang
                # This actually has an impact, don't remove this line
                context = {'lang': employee_lang}
                if localdict['result_name']:
                    rule_name = localdict['result_name']
                elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION',
                                   'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
                    if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
                        if rule.name == 'Double Holiday Pay':
                            rule_name = _('Double Holiday Pay')
                        if rule.struct_id.name == 'CP200: Employees 13th Month':
                            rule_name = _('Prorated end-of-year bonus')
                        else:
                            rule_name = _('Basic Salary')
                    elif rule.code == 'GROSS':
                        rule_name = _('Gross')
                    elif rule.code == 'DEDUCTION':
                        rule_name = _('Deduction')
                    elif rule.code == 'REIMBURSEMENT':
                        rule_name = _('Reimbursement')
                    elif rule.code == 'NET':
                        rule_name = _('Net Salary')
                else:
                    rule_name = rule.with_context(lang=employee_lang).name
                # create/overwrite the rule in the temporary results
                result[rule.code] = {
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule_name,
                    'note': html2plaintext(rule.note),
                    'salary_rule_id': rule.id,
                    'contract_id': localdict['contract'].id,
                    'employee_id': localdict['employee'].id,
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                }
        return result.values()

    def get_salary_rule_amount(self, salary_values, salary_rule_id):
        total = 0.0
        for value in salary_values:
            if value.get('salary_rule_id') == salary_rule_id:
                total = float(value.get('quantity')) * value.get('amount') * value.get('rate') / 100
        return total

    @api.depends('service_year', 'reason_id', 'reason_type', 'salary_rule_id')
    def _calc_end_of_service_compensation(self):
        for rec in self:
            amount = 0.0
            before_5years_compensation = 0
            after_5years_compensation = 0
            result = rec.compute_salary_rules(rec.emp_struct_id.rule_ids)
            total = rec.get_salary_rule_amount(result, rec.salary_rule_id.id)
            number = rec.service_year

            salary = rec.get_salary_rule_amount(result, rec.salary_rule_id.id)
            service_years = rec.service_year
            # if rec.reason_type == 'end_of_contract':
            #     amount = rec.reason_id.compute_end_of_contract_amount(total, number)
            # elif rec.reason_type == 'resignation':
            #     amount = rec.reason_id.compute_resignation_amount(total, number)
            # elif rec.reason_type == 'article_80' or rec.reason_type == 'probation_period':
            #     amount = 0.0
            # elif rec.reason_type == 'article_77':
            #     end_contract_rule_id = self.env['hr.end_of_service.reason'].search(
            #         [('reason_type', '=', 'end_of_contract')], limit=1)
            #     amount = end_contract_rule_id.compute_end_of_contract_amount(total, number)

            if rec.reason_type == 'end_of_contract':
                if service_years <= 5:
                    before_5years_compensation = service_years * 0.5 * salary
                    after_5years_compensation = 0
                    amount = service_years * 0.5 * salary
                elif service_years > 5:
                    before_5years_compensation = (5 * 0.5 * salary)
                    after_5years_compensation = ((service_years - 5) * salary)
                    amount = (5 * 0.5 * salary) + ((service_years - 5) * salary)

            elif rec.reason_type == 'article_77':
                if service_years <= 5:
                    before_5years_compensation = (service_years * 0.5 * salary)
                    after_5years_compensation = 0
                    amount = (service_years * 0.5 * salary)
                elif service_years > 5:
                    before_5years_compensation = (5 * 0.5 * salary)
                    after_5years_compensation = ((service_years - 5) * salary)
                    amount = (5 * 0.5 * salary) + ((service_years - 5) * salary)

            elif rec.reason_type == 'resignation':
                if service_years < 2:
                    amount = 0
                elif service_years <= 5:
                    before_5years_compensation = (service_years * 0.5 * salary) * (1 / 3)
                    amount = (service_years * 0.5 * salary) * (1 / 3)

                elif service_years < 10:
                    before_5years_compensation = (5 * 0.5 * salary) * (2 / 3)
                    after_5years_compensation = ((service_years - 5) * salary) * (2 / 3)
                    amount = ((5 * 0.5 * salary) + ((service_years - 5) * salary)) * (2 / 3)
                    # amount = ((1.0 / 3) * salary * 5) + ((2.0 / 3) * salary * (service_years - 5))

                elif service_years >= 10:
                    before_5years_compensation = (5 * 0.5 * salary)
                    after_5years_compensation = ((service_years - 5) * salary)
                    amount = (5 * 0.5 * salary) + ((service_years - 5) * salary)
            elif rec.reason_type == 'article_80' or rec.reason_type == 'probation_period':
                amount = 0
            else:
                amount = 0

            rec.end_of_service_compensation = amount
            rec.before_5years_compensation = before_5years_compensation
            rec.after_5years_compensation = after_5years_compensation

    @api.depends('reason_id', 'reason_type', 'salary_rule_id')
    def _calc_article_77_compensation(self):
        for rec in self:
            amount = 0.0
            result = rec.compute_salary_rules(rec.emp_struct_id.rule_ids)
            total = rec.get_salary_rule_amount(result, rec.salary_rule_id.id)
            if rec.reason_id.reason_type == 'article_77':
                amount = total * 2
            rec.article_77_compensation = amount

    def _get_remaining_leaves(self, employee_id):
        """ Helper to compute the remaining leaves for the current employees
            :returns dict where the key is the employee id, and the value is the remain leaves
        """
        eos_leave_type_ids = self.env['hr.leave.type'].search([('eos_computed', '=', True)])
        if eos_leave_type_ids and employee_id:
            self._cr.execute("""
                SELECT
                    sum(h.number_of_days) AS days
                FROM
                    (
                        SELECT holiday_status_id, number_of_days,
                            state, employee_id
                        FROM hr_leave_allocation
                        UNION ALL
                        SELECT holiday_status_id, (number_of_days * -1) as number_of_days,
                            state, employee_id
                        FROM hr_leave
                    ) h
                    join hr_leave_type s ON (s.id=h.holiday_status_id)
                WHERE
                    s.active = true AND h.state='validate' AND
                    s.requires_allocation='yes' AND
                    h.employee_id = %s AND
                    s.id in %s
                GROUP BY h.employee_id""", (employee_id, tuple(eos_leave_type_ids.ids)))
            f_data = self._cr.fetchone()
            res = f_data[0] if f_data != None else 0.0
        else:
            res = 0.0
        return res

    # def _get_unpaid_leaves(self):
    #     """ Helper to compute the unpaid leaves for the current employees
    #         :returns dict where the key is the employee id, and the value is the unpaid leaves
    #     """
    #     employee_id = self.employee_id.id
    #     eos_leave_type_ids = self.env['hr.leave.type'].search([('work_entry_type_id.code', '=', 'LEAVE90')])
    #     if eos_leave_type_ids and employee_id:
    #         self._cr.execute("""
    #             SELECT
    #                 sum(h.number_of_days) AS days
    #             FROM
    #                 (
    #                     SELECT holiday_status_id, number_of_days,
    #                         state, employee_id
    #                     FROM hr_leave
    #                 ) h
    #                 join hr_leave_type s ON (s.id=h.holiday_status_id)
    #             WHERE
    #                 s.active = true AND h.state='validate' AND
    #                 h.number_of_days > 21 AND
    #                 h.employee_id = %s AND
    #                 s.id in %s
    #             GROUP BY h.employee_id""", (employee_id, tuple(eos_leave_type_ids.ids)))
    #         f_data = self._cr.fetchone()
    #         res = f_data[0] if f_data != None else 0.0
    #     else:
    #         res = 0.0
    #     self.unpaid_leave = res

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

    @api.depends('date_of_join', 'date', 'employee_id')
    def _get_unpaid_leaves(self):
        """ Helper to compute the unpaid leaves for the current employees
            :returns dict where the key is the employee id, and the value is the unpaid leaves
        """
        accumulated_unpaid_leave = 0
        for rec in self:
            if rec.date_of_join and rec.date:
                first_year = rec.date_of_join.year
                last_year = rec.date.year

                leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                                                      ('holiday_status_id.name', '=', 'Unpaid Leave')])

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

    @api.depends('employee_id', 'service_year', 'reason_id', 'leave_rule_id', 'annual_leave_type')
    def _calc_remaining_leaves(self):
        last_date_current_year = datetime(datetime.now().year, 12, 31)
        difference = 0
        current_year_lost_allocation = 0.0

        for rec in self:
            if rec.date:
                difference = last_date_current_year.date() - rec.date  # Difference between last day in the year and last working day
                current_year_lost_allocation = (difference.days / 365) * rec.employee_id.annual_leave

            current_year_lost_allocation = round(current_year_lost_allocation)

            amount = 0.0
            if rec.annual_leave_type == 'working_days':
                number_of_days = 22
            else:
                number_of_days = 30
            eos_rule_id = rec.reason_id.eos_rule_ids.filtered(
                lambda c: c.from_year <= rec.service_year and c.to_year >= rec.service_year)
            # remaining = float_round(self._get_remaining_leaves(rec.employee_id.id), precision_digits=2)
            balance = self.env['hr.leave.balance'].sudo().search([('employee_id', '=', rec.employee_id.id)], limit=1)
            if balance:
                remaining = balance.remain
            else:
                remaining = 0

            remaining = remaining - current_year_lost_allocation

            # if eos_rule_id: # Removed so that leaves calculated despite of any reason
            result = rec.compute_salary_rules(rec.emp_struct_id.rule_ids)
            total = rec.get_salary_rule_amount(result, rec.leave_rule_id.id)
            amount = (total / number_of_days) * remaining
            rec.remaining_leaves = remaining
            rec.leave_compensation = amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(self._name)
        return super(EndOfService, self).create(vals_list)

    @api.depends('payslip_id.line_ids.amount')
    def _calc_amount(self):
        for record in self:
            payslip_line_ids = record.mapped('payslip_id.line_ids').filtered(
                lambda record: record.category_id.id != self.env.ref('hr_payroll.NET').id)
            record.amount = sum(payslip_line_ids.mapped('amount'))

    @api.depends('date_of_join', 'date', 'employee_id', )
    def _calc_org_service_year(self):
        for record in self:
            delta = relativeDelta(record.date, record.date_of_join)
            record.org_service_desc = delta_desc(delta)

    @api.depends('date_of_join', 'date', 'employee_id', 'deduct_unpaid_leave', 'unpaid_leave')
    def _calc_service_year(self):
        for record in self:

            if record.deduct_unpaid_leave:
                delta = relativeDelta(record.date - relativedelta(days=int(record.unpaid_leave)), record.date_of_join)
            else:
                delta = relativeDelta(record.date, record.date_of_join)
            record.service_desc = delta_desc(delta)
            service_month = (delta.years * 12) + (delta.months) + (delta.days / 30.0)
            service_year = service_month / 12
            record.service_year = service_year
            record.service_month = service_month
            record.days_of_service = delta.days if delta.days >= 0 else 0
            record.months_of_service = delta.months if delta.months >= 0 else 0
            record.years_of_service = delta.years if delta.years >= 0 else 0

    def unlink(self):
        if any(self.filtered(lambda record: record.state != 'draft')):
            raise UserError(_('You cannot delete a record which is not in draft state.'))

        for record in self:
            record.payslip_id.sudo().action_payslip_cancel()
            record.payslip_id.sudo().unlink()

        return super(EndOfService, self).unlink()

    def action_payslip(self):
        if not self.payslip_id:
            payslip = self.env['hr.payslip'].with_user(SUPERUSER_ID).create({'employee_id': self.employee_id.id,
                                                                             'name': _(
                                                                                 'End Of Service of the employee %s') % self.employee_id.name,
                                                                             'contract_id': self.contract_id.id,
                                                                             'struct_id': self.eos_structure_id.id,
                                                                             'date_from': self.date_of_join,
                                                                             'date_to': self.date,
                                                                             'end_of_service_id': self.id,
                                                                             'eos_amount': self.end_of_service_compensation,
                                                                             'eos_leave_amount': self.leave_compensation,
                                                                             'eos_article_77_amount': self.article_77_compensation,
                                                                             'eos_payslip': True
                                                                             })
            payslip_msg = _(
                "This payslip has been created from: <a href=# data-oe-model=hr.end_of_service data-oe-id=%d>%s</a>") % (
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
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'name': 'Pay slip',
            'res_id': self.payslip_id.id,
            'view_mode': 'form',
        }