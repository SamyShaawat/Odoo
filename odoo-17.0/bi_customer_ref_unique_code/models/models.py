# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_sequence(self):
        customer_seq = self.env['ir.sequence'].next_by_code('unique.code.sequence')
        return customer_seq

    customer_seq = fields.Char(string='Customer Unique Code ',default=_default_sequence)

class POSSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        res = super(POSSession, self)._loader_params_res_partner()
        fields = res.get('search_params').get('fields')
        fields.extend(['customer_seq'])
        res['search_params']['fields'] = fields
        return res

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def customer_code_button(self):
        res_partner1 = self.env['res.partner'].search([])
        for name in res_partner1:
            if not name.customer_seq: 
                name['customer_seq'] = self.env['ir.sequence'].next_by_code('unique.code.sequence')
                res_partner = self.env['res.partner'].browse(name.id)
                res = res_partner.update({'customer_seq': name['customer_seq']})
