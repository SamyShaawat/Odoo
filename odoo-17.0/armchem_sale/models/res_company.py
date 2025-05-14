# # -*- coding: utf-8 -*-
# # Part of Odoo. See LICENSE file for full copyright and licensing details.
# import base64
#
# from odoo import api, fields, models, _
# from odoo.modules.module import get_module_resource
#
#
# class ResCompany(models.Model):
#     _inherit = "res.company"
#
#     shipping_tax_state_ids = fields.Many2many('res.country.state', string='Shipping Tax',
#                                               help='Enable shipping tax for states')
