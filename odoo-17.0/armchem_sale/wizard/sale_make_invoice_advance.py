# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        commission_earned = 0
        if order.zone2_price == 'yes':
            commission_earned = (so_line.price_unit - (
                    so_line.product_id.zone2_price - so_line.product_id.list_price)) * so_line.qty_to_invoice * so_line.commission_percent
        else:
            commission_earned = so_line.price_unit * so_line.qty_to_invoice * so_line.commission_percent
        invoice_vals['invoice_line_ids'][0][2].update({
            'commission_earned': commission_earned / 100 if commission_earned else 0
        })
        return invoice_vals
