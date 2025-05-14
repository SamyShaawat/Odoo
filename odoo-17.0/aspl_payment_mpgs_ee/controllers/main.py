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

import pycountry
import requests
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
import logging
import json
import logging

_logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):

    # @http.route(['/get_mpgs_data'],  type='json', auth='public', methods=['POST'], csrf=False, website=True)
    # def get_mpgs_data(self, **kwargs):
    #     res = {}
    #     mpgs_id = request.env['payment.provider'].sudo().search([('code', '=', 'mpgs')], limit=1)
    #     website_order = request.website.sale_get_order()
    #     request_content = json.loads(request.httprequest.data)
    #     _logger = logging.getLogger(__name__)
    #     # Log the received payload
    #     _logger.info("Received payload: %s", request_content)
    #
    #     sale_order_id = request_content.get('sale_order_id')
    #     _logger.info("Extracted sale_order_id: %s", sale_order_id)
    #     if sale_order_id:
    #         sale_order_id = int(sale_order_id)
    #
    #     order = request.env['sale.order'].sudo().browse(sale_order_id) or website_order
    #     if not order:
    #         raise ValueError(f"Sale order with ID {sale_order_id} does not exist")
    #
    #     tx = order.transaction_ids.filtered(lambda t: t.state == 'draft')
    #     if not tx:
    #         raise ValueError("No draft transactions found for the sale order")
    #
    #     tx = tx[0]
    #     #tx = order.transaction_ids.filtered(lambda t: t.state == 'draft')[0]
    #     # tx = request.env['payment.transaction'].sudo().search([], limit=1)
    #     if tx:
    #         res['cust_email'] = tx.partner_id.email
    #         res['cust_phone'] = tx.sale_order_ids.partner_shipping_id.phone
    #         #res['cust_street'] = tx.partner_id.street[0:100]
    #         res['cust_street'] = tx.sale_order_ids.partner_shipping_id.street[0:100]
    #         res['cust_city'] = tx.sale_order_ids.partner_shipping_id.city
    #         res['cust_zip'] = tx.sale_order_ids.partner_shipping_id.zip
    #         res['cust_state_code'] = tx.sale_order_ids.partner_shipping_id.state_id.name
    #         if len(tx.partner_id.country_id.code) == 2:
    #             try:
    #                 country = pycountry.countries.get(alpha_2=(tx.partner_id.country_id.code).upper())
    #                 res['cust_country'] = country.alpha_3
    #             except Exception as e:
    #                 raise ValueError("Exception-", e)
    #         else:
    #             res['cust_country'] = (tx.partner_id.country_id.code).upper()
    #
    #         res['amount'] = tx.amount
    #         res['currency'] = tx.currency_id.name
    #
    #     for sale_order in tx.sale_order_ids:
    #         for line in sale_order.order_line:
    #             res['product_name'] = line.product_id.name
    #             res['order_name'] = tx.reference
    #             res['order_id'] = tx.id
    #
    #     """
    #     According to Country, Bank and merchant details interaction.operation can be change from
    #     res['interaction.operation'] = 'PURCHASE' or
    #     res['interaction.operation'] = 'AUTHORIZE'
    #     """
    #
    #     if mpgs_id:
    #         res['merchant_id'] = mpgs_id.merchant_id
    #         res['merchant_name'] = mpgs_id.merchant_name
    #         res['address1'] = mpgs_id.address1
    #         res['address2'] = mpgs_id.address2
    #         res['interaction.operation'] = 'PURCHASE'
    #     # res['interaction.operation'] = 'PURCHASE'
    #     base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     cancel_url = base_url + '/shop/payment'
    #     return_url = base_url + '/shop/completeCallback'
    #     # res['interaction.cancelUrl'] = cancel_url
    #     # res['interaction.returnUrl'] = return_url
    #     # Rest API
    #
    #     data = [('apiOperation', 'CREATE_CHECKOUT_SESSION'),
    #             ('apiPassword', mpgs_id.mpgs_secret_key),
    #             ('apiUsername', 'merchant.' + mpgs_id.merchant_id),
    #             ('merchant', mpgs_id.merchant_id),
    #             ('order.id', str(tx.id) + '' + tx.reference),
    #             ('order.amount', res['amount']),
    #             ('order.description', tx.reference),
    #             ('order.currency', res['currency']),
    #             ('interaction.operation', 'PURCHASE'),
    #             ('interaction.cancelUrl', cancel_url),
    #             ('interaction.returnUrl', return_url)
    #             ]
    #     '''
    #     According to country, bank and merchant details mpgs_links can differ
    #     '''
    #     if mpgs_id.state == 'enabled':
    #         # noinspection Pylint
    #         mpgs_form_url = 'https://banquemisr.gateway.mastercard.com/api/nvp/version/61'
    #     else:
    #         mpgs_form_url = 'https://banquemisr.gateway.mastercard.com/api/nvp/version/52'
    #     f = requests.post(mpgs_form_url, data=data)
    #
    #     data = str(f.content, 'utf-8').split('&')
    #
    #     session_Initiated = any(['result', 'SUCCESS'] == attr.split('=') for attr in data)
    #     if not session_Initiated:
    #         raise ValueError("Exception-session-not-Initiated")
    #         _logger.info("MPGS Notification Responce {}".format(f.content))
    #
    #     successIndicator = list(filter(lambda x: 'successIndicator' in x.split('='), data))
    #     successIndicator_value = successIndicator[0].split('=')[1]
    #     tx.write({
    #         'provider_reference': str(tx.id) + '' + tx.reference,
    #         'mpgs_Indicator': successIndicator_value,
    #     })
    #
    #     for each in data:
    #         if 'session.id' in each:
    #             res['session_id'] = each.split('=')[1]
    #         if 'session.version' in each:
    #             res['session_version'] = each.split('=')[1]
    #     return res

    @http.route(['/shop/completeCallback'], type='http', auth='public', csrf=False, save_session=False)
    def confirm_order_new(self, **post):
        if post and post.get('resultIndicator', False):
            # Check the integrity of the notification.
            payment_transaction = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'mpgs', post
            )
            if payment_transaction:
                payment_transaction._handle_notification_data('mpgs', post)
                return request.redirect('/payment/status')
            return request.redirect('/shop')
        return request.redirect('/shop')
