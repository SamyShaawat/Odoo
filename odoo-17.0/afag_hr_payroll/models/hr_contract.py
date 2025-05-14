# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class Contract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Contract Extension'

    total_wage = fields.Monetary(compute='_compute_wage_total')

    def _compute_wage_total(self):
        for rec in self:
            rec.total_wage = rec.wage + rec.l10n_sa_housing_allowance + rec.l10n_sa_transportation_allowance+ rec.l10n_sa_other_allowances

    def compute_settlement(self, payslip, code=None):
        result = 0.0
        settlement = self.env['hr.employee.settlement'].search(
            [('employee_id', '=', self.employee_id.id), ('state','=','done')]).filtered(lambda x:x.start_date <= payslip.date_from and payslip.date_to <= x.end_date)
        for rec in settlement:
            if rec.settlement_id.code == code:
                result = rec.amount
                if rec.sudo().settlement_id.type == "ded":
                    result *= -1
        return float(result)
