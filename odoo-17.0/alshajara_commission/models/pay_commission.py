from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    if_commission = fields.Boolean(string='Add Commission')

    commission_rate = fields.Float(string='Employees Commission')

    total_without_commission = fields.Float(string='Company Profit', compute='_compute_total_without_commission', store=True)

    commission_value = fields.Float(string='Employees Profit', compute='_compute_commission_value', store=True)

    employee_id = fields.Many2one('hr.employee')

    @api.depends('amount_total', 'commission_rate')
    def _compute_total_without_commission(self):
        for order in self:
            if order.if_commission:
                order.total_without_commission = order.amount_total - (order.amount_total * (order.commission_rate / 100))
            else:
                order.total_without_commission = order.amount_total

    @api.depends('total_without_commission', 'commission_rate')
    def _compute_commission_value(self):
        for order in self:
            if order.if_commission:
                order.commission_value = order.amount_total * (order.commission_rate / 100)
            else:
                order.commission_value = 0.0

    @api.constrains('commission_flat', 'commission_rate')
    def _check_commission_values(self):
    #     """Validation for commission amount and percentage."""
        for order in self:
    #         # 1. Commission Amount or percentage cannot be negative
            if order.commission_flat < 0 or order.commission_rate < 0:
                raise ValidationError("Commission Amount or Percentage cannot be negative.")
    #
    #         # 2. Amount cannot be more than Employees Commission
    #         if order.commission_flat > order.employees_commission:
    #             raise ValidationError("Commission Flat Amount cannot be more than the Employees Commission.")
    #
    #         # 3. Amount % cannot be more than 100
            if order.commission_rate > 100:
                raise ValidationError("Commission Percentage cannot be more than 100%.")



    def action_create_commission(self):
        if not self.order_line:
            raise ValueError("Order line must be set to create an invoice.")

        invoice_lines = []
        for line in self.order_line:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
            }))

        create_bill = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': self.date_order,
            'invoice_line_ids': invoice_lines
        })


        if not create_bill:
            raise ValueError("Failed to create the invoice.")

        return create_bill
    def open_bill(self):
        bill = self.action_create_commission()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': bill.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_expense(self):
        expense_model = self.env['hr.expense']

        if not self.employee_id:
            raise UserError("Please select an employee before creating an expense.")

        expense = expense_model.create({
            'employee_id': self.employee_id.id,
            'name': 'Expense related to Sale Order: {}'.format(self.name),
            'total_amount': self.commission_value,
            'date': fields.Date.today(),
            'currency_id': self.currency_id.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense',
            'res_model': 'hr.expense',
            'res_id': expense.id,
            'view_mode': 'form',
            'target': 'current',
        }