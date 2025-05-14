# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class UpsWsOut(models.Model):
    _name = 'web.upsws.out'
    _description = "upswsout"
    _rec_name = 'id'

    @api.depends('packagereference3')
    def _compute_order_id(self):
        for record in self:
            so = self.env['sale.order'].search([('name', '=', record.packagereference3)], limit=1)
            record.order_id = so.id if so else False

    packagereference3 = fields.Char(string='PackageReference3')
    packagereference2 = fields.Char(string='PackageReference2')
    shipmentinformationcollectiondate = fields.Char(string='ShipmentInformationCollectiondate')
    packagetrackingnumber = fields.Char(string='PackageTrackingNumber')
    packagepackagepublishedcharge = fields.Float(string='PackagePackagePublishedCharge')
    shipmentinformationvoidindicator = fields.Char(string='ShipmentInformationVoidIndicator')
    shipmentinformationhundredweight = fields.Char(string='ShipmentInformationHundredweight')
    shipmentinformationtotalshipmentpublishedcharge = fields.Float(
        string='ShipmentInformationTotalShipmentPublishedCharge')

    order_id = fields.Many2one('sale.order', compute='_compute_order_id', string='Order Reference', store=True,
                               ondelete='cascade', index=True, copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
