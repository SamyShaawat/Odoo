# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta


class CrmTeam(models.Model):
    _inherit = "crm.team"

    sales_department = fields.Selection([('outside', 'Outside'), ('inside', 'Inside')], string='Sales Department',
                                        default='outside')

    @api.onchange('sales_department')
    @api.depends('sales_department')
    def select_sales_man_group(self):
        users = self.env['res.users'].search([('name', '=', 'name')])
        if self.sales_department == 'inside':
            group = self.env['res.groups'].search([('name', '=', 'Inside Sales')], limit=1)
        elif self.sales_department == 'outside':
            group = self.env['res.groups'].search([('name', '=', 'Outside Sales')], limit=1)
        else:
            group = None
        if group:
            group.write({'users': [(4, user.id) for user in users]})
