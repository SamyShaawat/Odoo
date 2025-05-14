# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models



class UpsWs(models.Model):
    _name = 'web.upsws'
    _description = "upsws"
    _rec_name = 'id'

    from_name = fields.Char(string='FROM_NAME')
    from_addr1 = fields.Char(string='FROM_ADDR1')
    from_addr2 = fields.Char(string='FROM_ADDR2')
    from_city = fields.Char(string='FROM_CITY')
    from_st = fields.Char(string='FROM_ST')
    from_postal = fields.Char(string='FROM_POSTAL')
    from_country = fields.Char(string='FROM_COUNTRY')
    order_no = fields.Char(string='ORDER_NO')
    customer_no = fields.Char(string='CUSTOMER_NO')
    ship_name = fields.Char(string='SHIP_NAME')
    ship_addr1 = fields.Char(string='SHIP_ADDR1')
    ship_addr2 = fields.Char(string='SHIP_ADDR2')
    ship_city = fields.Char(string='SHIP_CITY')
    ship_st = fields.Char(string='SHIP_ST')
    ship_postal = fields.Char(string='SHIP_POSTAL')
    ship_country = fields.Char(string='SHIP_COUNTRY')
    ship_phone = fields.Char(string='SHIP_PHONE')
    cust_po = fields.Char(string='CUST_PO')
    service = fields.Char(string='SERVICE')
    billing = fields.Char(string='BILLING')
    pkg_type = fields.Char(string='PKG_TYPE')
    shipper = fields.Char(string='SHIPPER')
    order_lne = fields.Integer(string='ORDER_LNE')
    item_code = fields.Char(string='ITEM_CODE')
    weight = fields.Float(string='WEIGHT')
    tpcustno = fields.Char(string='TPCUSTNO')
    tpname = fields.Char(string='TPNAME')
    tpaddr1 = fields.Char(string='TPADDR1')
    tpaddr2 = fields.Char(string='TPADDR2')
    tpcity = fields.Char(string='TPCITY')
    tpstate = fields.Char(string='TPSTATE')
    tpcountry = fields.Char(string='TPCOUNTRY')
    tppostal = fields.Char(string='TPPOSTAL')
    tpphone = fields.Char(string='TPPHONE')
    tpfax = fields.Char(string='TPFAX')
    tpupsno = fields.Char(string='TPUPSNO')
    dbldimensionl = fields.Float(string='dblDimensionL')
    dbldimensionw = fields.Float(string='dblDimensionW')
    dbldimensionh = fields.Float(string='dblDimensionH')
    attention = fields.Char(string='Attention')
    order_date = fields.Datetime(string='ORDER_DATE')

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
