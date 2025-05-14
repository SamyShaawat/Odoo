from odoo import fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    eos_id = fields.Many2one('hr.eos.request')

    def action_payslip_done(self):
        # Add custom logic here before calling the original method
        result = super(HrPayslip, self).action_payslip_done()

        if self.eos_id:
            self.eos_id.state='paid'

        # Custom logic after the payslip is confirmed
        # For example, sending notifications, updating fields, etc.

        return result

class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"
    is_eos = fields.Boolean('Eos')
