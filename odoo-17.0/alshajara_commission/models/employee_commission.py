from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class EmployeeCommission(models.Model):
    _name = 'employee.commission'
    _description = 'Employee Commission'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    amount_percentage = fields.Float(string="Amount %")
    flat_amount = fields.Float(string="Flat Amount")
    total_flat_amount = fields.Float(compute='_compute_total_flat_amount')
    date_order = fields.Datetime(related='sale_order_id.date_order', string='Order Date', store=True)
    partner_id = fields.Many2one('res.partner',related='sale_order_id.partner_id', string='Customer', store=True)
    so_subtotal = fields.Monetary(string='Order Subtotal', related='sale_order_id.amount_untaxed', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    total_cost = fields.Float(string="Cost", related='sale_order_id.total_cost_po', store=True)
    profit = fields.Float(string="Profit", related='sale_order_id.profit', store=True)
    profit_percentage = fields.Float(string="Profit %", related='sale_order_id.profit_percentage', store=True)
    commission_percentage = fields.Float(string="Commission %", compute='_compute_commission_percentage', store=True)
    paid = fields.Boolean(string='Paid', readonly=True)



    @api.onchange('amount_percentage')
    def _onchange_amount_percentage(self):
        for line in self:
            if line.amount_percentage:
                line.flat_amount = (line.sale_order_id.employees_commission * line.amount_percentage) /100
        print("line.sale_order_id.employees_commission",line.sale_order_id.employees_commission,"line.amount_percentage",line.amount_percentage)
    @api.onchange('flat_amount')
    def _onchange_flat_amount(self):
        for line in self:
            if line.flat_amount and line.sale_order_id.employees_commission:
                if line.sale_order_id.employees_commission > 0:
                    line.amount_percentage = (line.flat_amount / line.sale_order_id.employees_commission) * 100
                else:
                    line.amount_percentage = 0.0
            else:
                line.amount_percentage = 0.0

    @api.depends('flat_amount')
    def _compute_total_flat_amount(self):
        for record in self:
            total_amount = sum(line.flat_amount for line in record.sale_order_id.commission_lines)
            record.total_flat_amount = total_amount

    @api.constrains('flat_amount', 'amount_percentage')
    def _check_commission_limits(self):
        for line in self:
            if line.flat_amount < 0 or line.amount_percentage < 0:
                raise ValidationError("Commission amount or percentage cannot be negative.")
            if line.total_flat_amount > line.sale_order_id.employees_commission:
                raise ValidationError("Commission amount cannot exceed the employee's total commission.")
            if line.amount_percentage > 100:
                raise ValidationError("Commission percentage cannot exceed 100.")

    @api.depends('flat_amount', 'profit')
    def _compute_commission_percentage(self):
        for record in self:
            record.commission_percentage = (record.flat_amount / record.profit) * 100 if record.profit else 0

    @api.depends('flat_amount', 'paid')
    def _compute_total_flat_amount(self):
        for record in self:
            if not record.paid:
                total = sum(self.search([
                    ('employee_id', '=', record.employee_id.id),
                    ('paid', '=', False)
                ]).mapped('flat_amount'))
                record.total_flat_amount = total
            else:
                record.total_flat_amount = 0.0



    def action_create_journal_entry(self):
        employee_totals = {}

        for record in self:
            if not record.paid:
                employee_id = record.employee_id.id
                flat_amount = record.flat_amount

                if employee_id not in employee_totals:
                    employee_totals[employee_id] = {
                        'employee': record.employee_id,
                        'total_flat_amount': 0.0,
                    }

                employee_totals[employee_id]['total_flat_amount'] += flat_amount


        for employee_id, values in employee_totals.items():
            employee = values['employee']
            total_flat_amount = values['total_flat_amount']

            company = employee.company_id
            if not company.commission_liability_account_id or not company.commission_payable_account_id:
                raise UserError(_("Please configure the company's commission liability and payable accounts."))

            journal = self.env['account.journal'].search([('code', '=', 'COM')], limit=1)
            if not journal:
                raise UserError(_("The commission journal (COM) does not exist."))


            move_vals = {
                'journal_id': journal.id,
                'date': fields.Date.today(),
                'ref': f"Pay Commission for {employee.name}",
                'line_ids': [
                    (0, 0, {
                        'account_id': company.commission_liability_account_id.id,
                        'partner_id': False,
                        'debit': total_flat_amount,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'account_id': company.commission_payable_account_id.id,
                        'partner_id': employee.work_contact_id.id,
                        'debit': 0.0,
                        'credit': total_flat_amount,
                    })
                ]
            }

            # create journal entry
            journal_entry = self.env['account.move'].create(move_vals)
            journal_entry.action_post()


            for record in self:
                if record.employee_id.id == employee_id:
                    record.paid = True
