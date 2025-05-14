# -*- coding: utf-8 -*-

import json
import time
from ast import literal_eval
from datetime import date, timedelta
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date

class Picking(models.Model):
    _inherit = "stock.picking"

    def _create_upsws(self):
        sale_id = self.sale_id
        order_lne = 0
        move_line_ids = self.move_line_ids_without_package if self.move_line_ids_without_package else self.move_line_ids
        vals = {
            'order_no': sale_id.name,
            'order_date': sale_id.date_order,
            'cust_po': sale_id.customer_po,
            'service': 'Ground',
            'billing': 'Prepaid',
            'pkg_type': 'Package',
            'shipper': '10022X',
            'order_lne': len(move_line_ids.ids),
            'tpcustno': '',
            'tpname': '',
            'tpaddr1': '',
            'tpaddr2': '',
            'tpcity': '',
            'tpstate': '',
            'tpcountry': '',
            'tppostal': '',
            'tpphone': '',
            'tpfax': '',
            'tpupsno': '',
            'attention': '',
        }
        if sale_id.company_id:
            from_name = sale_id.company_id.name
            if from_name.lower() == 'armchem':
                from_name = 'Armchem International Corp.'
            vals.update({
                'from_name': from_name,
                'from_addr1': sale_id.company_id.street,
                'from_addr2': sale_id.company_id.street2,
                'from_city': sale_id.company_id.city,
                'from_st': sale_id.company_id.state_id.code if sale_id.company_id.state_id else None,
                'from_postal': sale_id.company_id.zip,
                'from_country': sale_id.company_id.country_id.name if sale_id.company_id.country_id else None,
            })
        if sale_id.partner_id:
            vals.update({
                'customer_no': sale_id.partner_id.ref,
            })
        if sale_id.partner_shipping_id:
            vals.update({
                'ship_name': sale_id.partner_shipping_id.name,
                'ship_addr1': sale_id.partner_shipping_id.street,
                'ship_addr2': sale_id.partner_shipping_id.street2,
                'ship_city': sale_id.partner_shipping_id.city,
                'ship_st': sale_id.partner_shipping_id.state_id.code if sale_id.partner_shipping_id.state_id.code else None,
                'ship_postal': sale_id.partner_shipping_id.zip,
                'ship_country': sale_id.partner_shipping_id.country_id.name if sale_id.partner_shipping_id.country_id else None,
                'ship_phone': sale_id.partner_shipping_id.phone,
            })
        for line in move_line_ids:
            if line.product_id:
                vals.update({
                    'item_code': line.product_id.default_code,
                    'weight': line.product_id.weight,
                    'dbldimensionl': line.product_id.length,
                    'dbldimensionw': line.product_id.width,
                    'dbldimensionh': line.product_id.high,
                })
                for i in range(0, int(line.qty_done)):
                    self.env['web.upsws'].create(vals)

    def _action_done(self):
        res = super(Picking, self)._action_done()
        self._create_upsws()
        return res
