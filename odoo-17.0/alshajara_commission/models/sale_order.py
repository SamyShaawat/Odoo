import logging
from odoo import _, models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_ids = fields.One2many('purchase.order', 'sale_order_id', string="Related Purchase Orders")
    purchase_order_line_ids = fields.One2many('purchase.order.line', compute='_compute_purchase_order_lines',
                                              string="Purchased Products")
    total_cost_po = fields.Float(string="Total PO", compute="_compute_total_cost_po")
    profit = fields.Float(string="Profit", compute="_compute_profit")
    profit_percentage = fields.Float(string="Profit Percentage", compute="_compute_profit_percentage",
                                     widget='percentage')

    add_commission = fields.Boolean(string="Add Commission")
    commission_percentage = fields.Float(string="Commission Percentage", related='company_id.commission_percentage')
    company_profit = fields.Float(string="Company Profit", compute="_compute_company_profit")
    employees_commission = fields.Float(string="Employees Commission", compute="_compute_employees_commission")
    commission_amount = fields.Float(string="Commission Amount", compute='_compute_commission_amount', store=True)
    commission_paid = fields.Boolean(string="Commission Paid", default=False)
    commission_lines = fields.One2many('employee.commission', 'sale_order_id', string="Commission Table")
    is_button_clicked = fields.Boolean(string="Is Button Clicked", default=False)

    @api.depends('purchase_order_ids.order_line')
    def _compute_purchase_order_lines(self):
        for order in self:
            all_lines = self.env['purchase.order.line']
            for purchase_order in order.purchase_order_ids:
                all_lines |= purchase_order.order_line
            order.purchase_order_line_ids = all_lines

    @api.depends('purchase_order_ids')
    def _compute_total_cost_po(self):
        for order in self:
            order.total_cost_po = sum(po.amount_untaxed for po in order.purchase_order_ids)

    @api.depends('amount_untaxed', 'total_cost_po')
    def _compute_profit(self):
        for order in self:
            order.profit = order.amount_untaxed - order.total_cost_po

    @api.depends('profit', 'amount_untaxed')
    def _compute_profit_percentage(self):
        for order in self:
            order.profit_percentage = (order.profit / order.amount_untaxed * 100) if order.amount_untaxed else 0.0

    @api.depends('profit', 'add_commission', 'commission_percentage')
    def _compute_company_profit(self):
        for order in self:
            if order.add_commission and order.profit:
                order.company_profit = order.profit * (1 - (order.commission_percentage ))
            else:
                order.company_profit = order.profit

    @api.depends('profit', 'add_commission', 'commission_percentage')
    def _compute_employees_commission(self):
        for order in self:
            if order.add_commission and order.profit:
                order.employees_commission = order.profit * (order.commission_percentage )
            else:
                order.employees_commission = 0.0

    @api.depends('profit', 'add_commission', 'commission_percentage')
    def _compute_commission_amount(self):
        for order in self:
            if order.add_commission and order.profit:
                order.commission_amount = order.profit * (order.commission_percentage / 100)
            else:
                order.commission_amount = 0.0



    def action_create_journal_entry(self):
        for record in self:
            # if record.is_button_clicked:
            #     raise UserError(
            #         _("The journal entry for this commission has already been created, it cannot be created again."))

            company = record.company_id
            if not company.commission_liability_account_id or not company.commission_payable_account_id:
                raise UserError(_("Please configure the company's commission liability and payable accounts."))

            journal = self.env['account.journal'].search([('code', '=', 'COM')], limit=1)
            if not journal:
                raise UserError(_("The commission journal (COM) does not exist."))

            # total_commission_amount = sum(line.flat_amount for line in record.commission_lines)
            # print("total_commission_amount", total_commission_amount)
            move_vals = {
                'journal_id': journal.id,
                'date': fields.Date.today(),
                'ref': f"Commission for {record.name}",
                'line_ids': [
                    (0, 0, {
                        'account_id': company.commission_expense_account_id.id,
                        'partner_id': False,
                        'debit': sum(line.flat_amount for line in record.commission_lines),
                        'credit': 0.0,
                    })
                ]
            }

            # Process each commission line for employees and add liability lines
            for commission_line in record.commission_lines:
                employee = commission_line.employee_id
                print("commission_line.flat_amount", commission_line.flat_amount)
                # Add a liability line for each employee
                move_vals['line_ids'].append(
                    (0, 0, {
                        'account_id': company.commission_liability_account_id.id,
                        'partner_id': employee.work_contact_id.id,  # Partner is the employee's work contact
                        'debit': 0.0,
                        'credit': commission_line.flat_amount,
                    })
                )

            journal_entry = self.env['account.move'].create(move_vals)
            journal_entry.action_post()

            record.commission_paid = True
            record.is_button_clicked = True


