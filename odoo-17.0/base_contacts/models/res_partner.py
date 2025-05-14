# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command


class Partner(models.Model):
    _inherit = "res.partner"

    customer_id = fields.Char(string='Customer ID')
    vendor_id = fields.Char(string='Vendor ID')

    # _sql_constraints = [
    #     ('customer_company_uniq', 'unique (customer_id,company_id)', 'The customer id must be unique per company !'),
    #     ('vendor_company_uniq', 'unique (vendor_id,company_id)', 'The vendor id must be unique per company !'),
    # ]

    @api.model
    def create(self, vals):
        print(vals)
        # print(vals['customer_rank'])
        result = super(Partner, self).create(vals)
        if not result.parent_id and result.customer_rank:
            result.customer_id = self.env['ir.sequence'].next_by_code('res.customer')
        elif not result.parent_id and result.supplier_rank:
            result.vendor_id = self.env['ir.sequence'].next_by_code('res.vendor')
        return result

    @api.model
    def _action_re_generate_seq(self):
        # partners = request.env['res.partner'].search([('parent_id', '=', False), ('customer_id', '=', False), ('vendor_id', '=', False)])
        partners = self.env['res.partner'].search([('parent_id', '=', False)])
        print(partners)
        for partner in partners:
            vals = {}
            if partner.customer_rank:
                if partner.ref:
                    vals['customer_id'] = f'C{partner.ref}'
                else:
                    vals['customer_id'] = self.env['ir.sequence'].next_by_code('res.customer')
            if partner.supplier_rank:
                if partner.ref:
                    vals['vendor_id'] = f'V{partner.ref}'
                else:
                    vals['vendor_id'] = self.env['ir.sequence'].next_by_code('res.vendor')

            if vals:
                partner.write(vals)
