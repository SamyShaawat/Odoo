# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    zone = fields.Char(string='Zone')

    def write(self, vals):
        res = super(DeliveryCarrier, self).write(vals)
        print(vals)
        if 'zone' in vals:
            if vals['zone'] == '1':
                pass
            elif vals['zone'] == '2':
                pass
            else:
                raise exceptions.UserError(_('ZONE MUST EQUAL 1 OR 2'))
        return res


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    zone = fields.Char(string='Zone', related='carrier_id.zone')
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string="Shipping Method",
        help="Choose the method to deliver your goods",
        required=True,
    )

    @api.depends('zone')
    @api.onchange('zone')
    def get_carrier_ids(self):
        for rec in self:
            if rec.zone:
                if rec.zone == '1':
                    res = {}
                    res['domain'] = {'carrier_id': [('zone', '=', '1')]}
                    return res
                elif rec.zone == '2':
                    res = {}
                    res['domain'] = {'carrier_id': [('zone', '=', '2')]}
                    return res
                else:
                    res = {}
                    return res
