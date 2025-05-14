# # -*- coding: utf-8 -*-
#
# from odoo import api, fields, models, Command, _
#
#
# class AccountMove(models.Model):
#     _inherit = "account.move"
#
#     @api.depends('invoice_line_ids')
#     def _compute_total_commission_earned(self):
#         for move in self:
#             move.total_commission_earned = sum(move.invoice_line_ids.mapped('commission_earned'))
#
#     total_commission_earned = fields.Float(string='Total Commission Earned', compute='_compute_total_commission_earned',
#                                            digits='Commission', store=True, default=0.0)
#
#     def action_compute_commission(self):
#         ''' Compute commission '''
#         self.ensure_one()
#         for line in self.invoice_line_ids:
#             if line.sale_line_ids.qty_delivered:
#                 commission_price_unit = line.sale_line_ids.commission_earned / line.sale_line_ids.qty_delivered
#                 line.commission_earned = line.quantity * commission_price_unit
#         self._compute_total_commission_earned()
#
#     def action_post(self):
#         # self.action_compute_commission()
#         moves_with_payments = self.filtered('payment_id')
#         other_moves = self - moves_with_payments
#         if moves_with_payments:
#             moves_with_payments.payment_id.action_post()
#         if other_moves:
#             other_moves._post(soft=False)
#         return False
#
#
# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"
#
#     @api.depends('product_id')
#     def _compute_standard_price(self):
#         for line in self:
#             line.standard_price = line.product_id.standard_price * line.quantity if line.product_id else 0
#
#     # @api.depends('product_id', 'quantity')
#     # def _compute_list_price(self):
#     #     for line in self:
#     #         line.list_price = line.product_id.list_price * line.quantity if line.product_id else 0
#     #
#     # @api.depends('product_id', 'quantity', 'standard_price')
#     # def _compute_loaded_cost(self):
#     #     for line in self:
#     #         line.loaded_cost = line.standard_price * 1.07 if line.product_id else 0
#     #
#     # @api.depends('product_id', 'quantity', 'loaded_cost')
#     # def _compute_profit_price(self):
#     #     for line in self:
#     #         profit_price = 0
#     #         if line.product_id:
#     #             profit_price = line.price_subtotal - line.loaded_cost - line.commission_earned
#     #         line.profit_price = profit_price if profit_price > 0 else 0
#     #
#     # @api.depends('product_id', 'quantity', 'profit_price')
#     # def _compute_profit_percent(self):
#     #     for line in self:
#     #         profit_percent = 0
#     #         if line.product_id and line.price_subtotal > 0:
#     #             profit_percent = line.profit_price / line.price_subtotal
#     #         line.profit_percent = profit_percent
#
#     commission_earned = fields.Float(string='Commission Earned', digits='Commission', default=0.0, readonly=True)
#     standard_price = fields.Float(string='Cost Price', compute='_compute_standard_price', digits='Cost Price',
#                                   groups="account.group_account_readonly", store=True, default=0.0)
#     # list_price = fields.Float(string='List Price', compute='_compute_list_price', digits='List Price', store=True,
#     #                           default=0.0)
#     # loaded_cost = fields.Float(string='Loaded Cost', compute='_compute_loaded_cost', digits='Loaded Cost', store=True,
#     #                            default=0.0)
#     # profit_price = fields.Float(string='Profit Price', compute='_compute_profit_price', digits='Profit Price',
#     #                             store=True, default=0.0)
#     # profit_percent = fields.Float(string='Profit Percent', compute='_compute_profit_percent', digits='Profit Percent',
#     #                               store=True, default=0.0)
