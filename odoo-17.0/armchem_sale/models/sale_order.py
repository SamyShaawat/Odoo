# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _, exceptions
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('pricelist_id', 'order_line')
    def _compute_total_commission_earned(self):
        for line in self:
            line.total_commission_earned = sum(line.order_line.mapped('commission_earned'))

    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], store=True,
                                  ondelete="restrict")
    customer_po = fields.Char(string='Customer PO', required=True)
    zone2_price = fields.Selection(
        selection=[('yes', 'Yes'), ('no', 'No')], string='Zone2 Price', required=True, default='yes', tracking=True)
    total_commission_earned = fields.Float(string='Total Commission Earned', compute='_compute_total_commission_earned',
                                           digits='Commission', store=True, default=0.0)

    # def write(self, vals):
    #     res = super().write(vals)
    #     return res
    
    
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.pricelist_id and self.env.user.has_group('armchem_sale.group_zone_2') and res.zone2_price == 'yes':
            pricelist_ids = self.env['product.pricelist'].search([('name', 'ilike', res.pricelist_id.name)])
            pricelist_ids = pricelist_ids.filtered(lambda p: p.name.split('-')[0].strip().upper() == 'ZONE2')
            if pricelist_ids:
                res.pricelist_id = pricelist_ids[0].id
                query = ("""
                    update sale_order set pricelist_id = %d where id =  %d
                """) % (pricelist_ids[0].id, res.id)
                self.env.cr.execute(query)

        else:
            if res.pricelist_id and not self.env.user.has_group(
                    'armchem_sale.group_zone_2') and res.zone2_price == 'yes':
                pricelist_ids = self.env['product.pricelist'].search([('name', 'ilike', res.pricelist_id.name)])
                pricelist_ids = pricelist_ids.filtered(lambda p: p.name.split('-')[0].strip().upper() == 'ZONE2')
                if pricelist_ids:
                    res.pricelist_id = pricelist_ids[0].id
                    query = ("""
                        update sale_order set pricelist_id = %d where id =  %d
                    """) % (pricelist_ids[0].id, res.id)
                    self.env.cr.execute(query)

            else:
                res.zone2_price = 'no'
                res.pricelist_id = res.partner_id.property_product_pricelist.id if res.partner_id and res.partner_id.property_product_pricelist else False
                if res.partner_id and res.partner_id.property_product_pricelist:
                    query = ("""
                        update sale_order set pricelist_id = %d where id =  %d
                    """) % (res.partner_id.property_product_pricelist.id, res.id)
                    self.env.cr.execute(query)

        return res

    @api.onchange('zone2_price')
    def _onchange_zone2_price(self):
        # if self.pricelist_id and self.zone2_price == 'yes':
        if self.pricelist_id and self.env.user.has_group('armchem_sale.group_zone_2') and self.zone2_price == 'yes':
            pricelist_ids = self.env['product.pricelist'].search([('name', 'ilike', self.pricelist_id.name)])
            pricelist_ids = pricelist_ids.filtered(lambda p: p.name.split('-')[0].strip().upper() == 'ZONE2')
            if pricelist_ids:
                self.pricelist_id = pricelist_ids[0].id
                query = ("""
                    update sale_order set pricelist_id = %d where id =  %d
                """) % (pricelist_ids[0].id, self._origin.id)
                self.env.cr.execute(query)

        else:
            if self.pricelist_id and not self.env.user.has_group(
                    'armchem_sale.group_zone_2') and self.zone2_price == 'yes':
                pricelist_ids = self.env['product.pricelist'].search([('name', 'ilike', self.pricelist_id.name)])
                pricelist_ids = pricelist_ids.filtered(lambda p: p.name.split('-')[0].strip().upper() == 'ZONE2')
                if pricelist_ids:
                    self.pricelist_id = pricelist_ids[0].id
                    query = ("""
                        update sale_order set pricelist_id = %d where id =  %d
                    """) % (pricelist_ids[0].id, self._origin.id)
                    self.env.cr.execute(query)

            else:
                self.zone2_price = 'no'
                self.pricelist_id = self.partner_id.property_product_pricelist.id if self.partner_id and self.partner_id.property_product_pricelist else False
                if self.partner_id and self.partner_id.property_product_pricelist:
                    query = ("""
                        update sale_order set pricelist_id = %d where id =  %d
                    """) % (self.partner_id.property_product_pricelist.id, self._origin.id)
                    self.env.cr.execute(query)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()      
        # self.zone2_price = 'yes' if self.partner_id and self.env.user.has_group('armchem_sale.group_zone_2') else 'no'
        # self._onchange_zone2_price()
        # SOFTHEALER CODE  
        if not self.env.context.get('website_id',False):
            self.zone2_price = 'yes' if self.partner_id and self.env.user.has_group('armchem_sale.group_zone_2') else 'no'
            self._onchange_zone2_price()
        # SOFTHEALER CODE
        return res

    @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    def onchange_partner_shipping_id(self):
        res = super(SaleOrder, self).onchange_partner_shipping_id()
        for line in self.order_line:
            line.product_id_change()
        return res

    def action_quotation_send(self):
        self.ensure_one()
        context = self._context.copy()
        res = super(SaleOrder, self.with_context(context)).action_quotation_send()
        for line in self.order_line:
            line._validate_discount_amount()
        return res

    def action_confirm(self):
        for line in self.order_line:
            if line.product_id.categ_id.name == 'Deliveries':
                shipping = self.env['delivery.carrier'].search([('product_id', '=', line.product_id.id)], limit=1)
                if shipping.zone == '1' and self.zone2_price == 'no':
                    pass
                elif shipping.zone == '2' and self.zone2_price == 'yes':
                    pass
                else:
                    raise exceptions.UserError(_('Zone Pricing And Shipping Method Are Mismatched'))
        context = self._context.copy()
        for line in self.order_line:
            line._validate_discount_amount()
        super(SaleOrder, self.with_context(context)).action_confirm()

    def action_compute_commission(self):
        ''' Compute commission '''
        self.ensure_one()
        for line in self.order_line:
            line._compute_discount_amount()
            line._compute_commission_rate()
            line._compute_max_discount()
            line._compute_commission_percent()
            line._compute_commission_earned()
        self._compute_total_commission_earned()

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['customer_po'] = self.customer_po
        invoice_vals['zone2_price'] = self.zone2_price
        return invoice_vals

    def _create_delivery_line(self, carrier, price_unit):
        sol = super(SaleOrder, self)._create_delivery_line(carrier, price_unit)
        if self.fiscal_position_id and self.fiscal_position_id.name.lower() == 'tax exempt':
            sol.tax_id = False
        elif self.partner_shipping_id and self.partner_shipping_id.zip and self.partner_shipping_id.zip:
            # taxs = self.env['account.tax'].search([('name', 'ilike', self.partner_shipping_id.zip)])
            # SOFTHEALER CODE
            taxs = self.env['account.tax'].search([
                ('name', 'ilike', self.partner_shipping_id.zip),
                ('company_id', '=', self.env.company.id),                
            ])
            # SOFTHEALER CODE
            if sol.product_id.default_code and sol.product_id.default_code.upper().startswith("DELIVERY"):
                if self.partner_shipping_id.state_id and self.partner_shipping_id.state_id.id in self.company_id.shipping_tax_state_ids.ids:
                    sol.tax_id = taxs
            else:
                sol.tax_id = taxs
        return sol

    def action_open_delivery_wizard(self):
        view_id = self.env.ref('delivery.choose_delivery_carrier_view_form').id
        if self.env.context.get('carrier_recompute'):
            name = _('Update shipping cost')
            carrier = self.carrier_id
        else:
            name = _('Add a shipping method')
            carrier = (
                    self.with_company(self.company_id).partner_shipping_id.property_delivery_carrier_id
                    or self.with_company(
                self.company_id).partner_shipping_id.commercial_partner_id.property_delivery_carrier_id
            )
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.delivery.carrier',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_carrier_id': carrier.id,
                'default_zone': '1' if self.zone2_price == 'no' else '2',
            }
        }

    # @api.onchange('zone2_price')
    # def _zone2_price_restriction(self):
    #     shippings = self.env['delivery.carrier'].search([])
    #     for shipping in shippings:
    #         for line in self.order_line:
    #             if line.product_id.id == shipping.product_id.id:
    #                 raise exceptions.UserError(_('Remove Shipping First So You Can Change'))
