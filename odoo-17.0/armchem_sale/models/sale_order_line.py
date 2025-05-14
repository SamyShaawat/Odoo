# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_product_price_rule(self):
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.order_id.partner_id.lang)
        product_context.update({
            'partner': self.order_id.partner_id,
            'quantity': self.product_uom_qty,
            'date': self.order_id.date_order,
            'pricelist': self.order_id.pricelist_id.id,
        })

        price, rule_id = self.order_id.pricelist_id.with_context(product_context)._get_product_price_rule(
            self.product_id,
            self.product_uom_qty or 1.0,
            self.order_id.partner_id)
        return price, rule_id

    @api.depends('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _compute_discount_amount(self):
        for line in self:
            discount_amount = 0
            if line.product_id:
                price, rule_id = line._get_product_price_rule()
                if rule_id and line.price_unit < price:
                    if price != 0:
                        discount_amount = 1 - (line.price_unit / price)
                        discount_amount = discount_amount * 100 if discount_amount > 0 else 0
                    else:
                        discount_amount = 1 - (line.price_unit / 1)
                        discount_amount = discount_amount * 100 if discount_amount > 0 else 0
                elif not rule_id and line.product_id.list_price:
                    if line.product_id.list_price != 0:
                        discount_amount = 1 - (line.price_unit / line.product_id.list_price)
                        discount_amount = discount_amount * 100 if discount_amount > 0 else 0
                    else:
                        discount_amount = 1 - (line.price_unit / 1)
                        discount_amount = discount_amount * 100 if discount_amount > 0 else 0
            line.discount_amount = discount_amount

    @api.depends('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _compute_commission_rate(self):
        for line in self:
            if line.product_id and line.product_id.categ_id:
                line.commission_rate = line.product_id.categ_id.cat_commission
            else:
                line.commission_rate = 0

    @api.depends('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _compute_max_discount(self):
        for line in self:
            if line.product_id and line.product_id.categ_id:
                line.max_discount = line.product_id.categ_id.max_discount
            else:
                line.max_discount = 0

    @api.depends('commission_rate', 'discount_amount')
    def _compute_commission_percent(self):
        for line in self:
            commission_percent = 0
            if line.product_id:
                price, rule_id = line._get_product_price_rule()
                if rule_id:
                    rule = self.env['product.pricelist.item'].browse(rule_id)
                    if rule.applied_on == '1_product':
                        commission_percent = rule.commission_percent
                    else:
                        commission_percent = line.commission_rate - line.discount_amount
                else:
                    commission_percent = line.commission_rate - line.discount_amount
            line.commission_percent = commission_percent if commission_percent > 0 else 0

    @api.depends('price_total', 'commission_percent', 'qty_delivered')
    def _compute_commission_earned(self):
        for line in self:
            if line.product_id:
                if line.order_id.zone2_price == 'yes' and line.order_id.state == 'sale':
                    commission_earned = (line.price_unit - (
                            line.product_id.zone2_price - line.product_id.list_price)) * line.qty_delivered * line.commission_percent
                elif line.order_id.zone2_price == 'yes':
                    commission_earned = (line.price_unit - (
                            line.product_id.zone2_price - line.product_id.list_price)) * line.product_uom_qty * line.commission_percent
                elif line.order_id.zone2_price == 'no' and line.order_id.state == 'sale':
                    commission_earned = line.price_unit * line.qty_delivered * line.commission_percent
                else:
                    commission_earned = line.price_unit * line.product_uom_qty * line.commission_percent
                line.commission_earned = commission_earned / 100 if commission_earned else 0
            else:
                line.commission_earned = 0

    @api.depends('product_id', 'product_uom_qty')
    def _compute_standard_price(self):
        for line in self:
            line.standard_price = line.product_id.standard_price * line.product_uom_qty if line.product_id else 0

    @api.depends('product_id', 'product_uom_qty')
    def _compute_list_price(self):
        for line in self:
            line.list_price = line.product_id.list_price * line.product_uom_qty if line.product_id else 0

    @api.depends('product_id', 'product_uom_qty', 'standard_price')
    def _compute_loaded_cost(self):
        for line in self:
            line.loaded_cost = line.standard_price * 1.07 if line.product_id else 0

    @api.depends('product_id', 'product_uom_qty', 'loaded_cost')
    def _compute_profit_price(self):
        for line in self:
            profit_price = 0
            if line.product_id:
                profit_price = line.price_subtotal - line.loaded_cost - line.commission_earned
            line.profit_price = profit_price if profit_price > 0 else 0

    @api.depends('product_id', 'product_uom_qty', 'profit_price')
    def _compute_profit_percent(self):
        for line in self:
            profit_percent = 0
            if line.product_id and line.price_subtotal > 0:
                profit_percent = line.profit_price / line.price_subtotal
            line.profit_percent = profit_percent

    # unit_list_price = fields.Float(string='Unit List Price', default=0.0)
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount', digits='Discount',
                                   store=True, default=0.0)
    commission_rate = fields.Float(string='Commission Rate', compute='_compute_commission_rate', digits='Commission',
                                   store=True, default=0.0)
    max_discount = fields.Float(string='Maximum Discount', compute='_compute_max_discount', digits='Discount',
                                store=True, default=0.0)
    commission_percent = fields.Float(string='Commission %', compute='_compute_commission_percent', digits='Commission',
                                      store=True, default=0.0)
    commission_earned = fields.Float(string='Commission Earned', compute='_compute_commission_earned',
                                     digits='Commission', store=True, default=0.0)
    standard_price = fields.Float(string='Cost Price', compute='_compute_standard_price',
                                  groups="account.group_account_readonly", digits='Cost Price', store=True, default=0.0)
    list_price = fields.Float(string='List Price', compute='_compute_list_price', digits='List Price', store=True,
                              default=0.0)
    loaded_cost = fields.Float(string='Loaded Cost', compute='_compute_loaded_cost', digits='Loaded Cost', store=True,
                               default=0.0)
    profit_price = fields.Float(string='Profit Price', compute='_compute_profit_price', digits='Profit Price',
                                store=True, default=0.0)
    profit_percent = fields.Float(string='Profit Percent', compute='_compute_profit_percent', digits='Profit Percent',
                                  store=True, default=0.0)

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        partner_shipping_id = self.order_id.partner_shipping_id
        if self.product_id and self.order_id.fiscal_position_id and self.order_id.fiscal_position_id.name.lower() == 'tax exempt':
            self.tax_id = False
        elif partner_shipping_id and partner_shipping_id.zip and self.product_id:
            # taxs = self.env['account.tax'].search([
            #     ('name', 'ilike', partner_shipping_id.zip)])
            # SOFTHEALER CODE
            taxs = self.env['account.tax'].search([
                ('name', 'ilike', partner_shipping_id.zip),
                ('company_id', '=', self.env.company.id),                
            ])
             # SOFTHEALER CODE
            if self.product_id.default_code and self.product_id.default_code.upper().startswith("DELIVERY"):
                if partner_shipping_id.state_id and partner_shipping_id.state_id.id in self.order_id.company_id.shipping_tax_state_ids.ids:
                    self.tax_id = taxs
            else:
                self.tax_id = taxs
          
        return res

    # def _prepare_invoice_line(self, **optional_values):
    #     self.ensure_one()
    #     res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
    #     commission_earned = (self.price_subtotal * self.commission_percent) / 100
    #     unit_commission_earned = commission_earned / self.product_uom_qty if commission_earned else 0
    #     commission_earned = unit_commission_earned * self.qty_to_invoice
    #     res.update({
    #         'commission_earned': commission_earned
    #     })
    #     return res

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.order_id.zone2_price == 'yes':
            commission_earned = (self.price_unit - (
                    self.product_id.zone2_price - self.product_id.list_price)) * self.qty_delivered * self.commission_percent
        else:
            commission_earned = self.price_unit * self.qty_delivered * self.commission_percent
        res.update({
            'commission_earned': commission_earned / 100 if commission_earned else 0
        })
        return res

    def _validate_discount_amount(self):
        if not self.user_has_groups('armchem_product.group_armchem_discount_approver'):
            if self.discount_amount > self.max_discount:
                raise ValidationError(_(
                    'Approval needed for discount of this level. Contact approver.'
                ))
