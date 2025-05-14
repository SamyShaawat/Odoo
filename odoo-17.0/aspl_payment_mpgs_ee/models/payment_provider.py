# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from odoo.addons.payment import utils as payment_utils
from odoo.addons.aspl_payment_mpgs_ee import const
from odoo.exceptions import ValidationError
from odoo import fields, models
class AcquirerMasterCard(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('mpgs', "MPGS")], ondelete={'mpgs': 'set default'})
    merchant_id = fields.Char(string='Merchant Id', required_if_provider='mpgs', groups='base.group_user')
    merchant_name = fields.Char(string='Merchant Name', required_if_provider='mpgs', groups='base.group_user')
    mpgs_secret_key = fields.Char(string='MPGS Secret Key', required_if_provider='mpgs', groups='base.group_user')
    address1 = fields.Char(string="Address1", required_if_provider='mpgs', groups='base.group_user')
    address2 = fields.Char(string="Address2", required_if_provider='mpgs', groups='base.group_user')
    DEFAULT_PAYMENT_METHODS_CODES = [
         # Primary payment methods.
        'card',
        # Brand payment methods.
        'visa',
        'mastercard'
    ]

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'mpgs':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'mpgs').update({
            'support_manual_capture': 'partial',
            'support_refund': 'partial',
            'support_tokenization': True,
        })



