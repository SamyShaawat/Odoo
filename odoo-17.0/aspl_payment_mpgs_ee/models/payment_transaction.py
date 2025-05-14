#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
import logging
import requests
import random
import string
import pycountry
import json
import base64
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.aspl_payment_mpgs_ee_webhook.controllers.main import MpgsWebHook
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class PaymentTxmpgs(models.Model):
    _inherit = 'payment.transaction'

    mpgs_Indicator = fields.Char('mpgs Indicator')

    # def _create_payment(self, **extra_create_values):
    #     """Create an `account.payment` record for the current transaction.

    #     If the transaction is linked to some invoices, their reconciliation is done automatically.

    #     Note: self.ensure_one()

    #     :param dict extra_create_values: Optional extra create values
    #     :return: The created payment
    #     :rtype: recordset of `account.payment`
    #     """
    #     self.ensure_one()
    #     x=self.provider_id._get_code()
    #     y = self.provider_id.journal_id.inbound_payment_method_line_ids

    #     payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids \
    #         .filtered(lambda l: l.code == self.provider_id._get_code())
    #     payment_values = {
    #         'amount': abs(self.amount),  # A tx may have a negative amount, but a payment must >= 0
    #         'payment_type': 'inbound' if self.amount > 0 else 'outbound',
    #         'currency_id': self.currency_id.id,
    #         'partner_id': self.partner_id.commercial_partner_id.id,
    #         'partner_type': 'customer',
    #         'journal_id': self.provider_id.journal_id.id,
    #         'company_id': self.provider_id.company_id.id,
    #         'payment_method_line_id': payment_method_line.id,
    #         'payment_token_id': self.token_id.id,
    #         'payment_transaction_id': self.id,
    #         'ref': self.reference,
    #         **extra_create_values,
    #     }
    #     payment = self.env['account.payment'].create(payment_values)
    #     payment.action_post()

    #     # Track the payment to make a one2one.
    #     self.payment_id = payment

    #     if self.invoice_ids:
    #         self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()

    #         (payment.line_ids + self.invoice_ids.line_ids).filtered(
    #             lambda line: line.account_id == payment.destination_account_id
    #                          and not line.reconciled
    #         ).reconcile()

    #     return payment

    def _get_processing_values(self):
        res = super()._get_processing_values()
        return res

    def _get_specific_rendering_values(self, processing_values, callback_url=False, graph_ql_redirect_url=False):
        """ Override to return APS-specific processing values.

        :param dict processing_values: The generic processing values of the transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'mpgs':
            return res
        res = {}
        mpgs_id = request.env['payment.provider'].sudo().search([('code', '=', 'mpgs')], limit=1)

        # try:
        #     request_content = json.loads(request.httprequest.data)
        # except json.JSONDecodeError:
        #     return {"error": "Invalid JSON data"}
        # print('-----------------------------------------222')
        #
        # _logger = logging.getLogger(__name__)
        # # Log the received payload
        # _logger.info("Received payload: %s", request_content)
        order = self.sale_order_ids
        if not order:
            raise ValueError(f"Sale order does not exist")
        tx = self
        if not tx:
            raise ValueError("No draft transactions found for the sale order")
        if tx:
            cust_email = tx.partner_id.email
            cust_phone = tx.sale_order_ids.partner_shipping_id.phone
            amount = tx.amount
            currency = tx.currency_id.name
            description = tx.reference
            order_id = tx.id

        # Set Merchant Information
        if mpgs_id:
            merchant_id = mpgs_id.merchant_id
            password = mpgs_id.mpgs_secret_key
            merchant_name = mpgs_id.merchant_name
            address1 = mpgs_id.address1
            address2 = mpgs_id.address2
        # Generate Base64-encoded credentials
        auth_string = f"merchant.{merchant_id}:{password}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        headers = {
            'Content-Type': 'text/plain',
            'Authorization': f"Basic {auth_encoded}"
        }
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        cancel_url = f"{base_url}/shop/payment"
        return_url = f"{base_url}/{callback_url}" if graph_ql_redirect_url else f"{base_url}/shop/completeCallback"
        notify_url = f"{base_url}{MpgsWebHook.webhook_url}"
        data = {
            "apiOperation": "INITIATE_CHECKOUT",
            "interaction": {
                "operation": "PURCHASE",
                "cancelUrl": cancel_url,
                "returnUrl": return_url,
                "merchant": {
                    "name": merchant_name,
                    "address": {
                        "line1": address1,
                        "line2": address2,
                    },
                },
                "displayControl": {
                    "billingAddress": 'HIDE',
                },
            },

            "order": {
                "currency": currency,
                "amount": str(amount),
                "id": order_id,
                "description": description,
                # "notificationUrl": notify_url
            },
            "customer": {
                "email": cust_email,
                "phone": cust_phone
            },

        }
        if mpgs_id.state == 'enabled':
            mpgs_form_url = 'https://banquemisr.gateway.mastercard.com/api/rest/version/100/merchant/{}/session'.format(
                merchant_id)
        else:
            raise ValueError("The payment is not enabled. ")
        # Make the POST request to create session
        response = requests.post(mpgs_form_url, headers=headers, json=data)
        response_data = response.json()
        # Handle API response
        if response_data.get("result") == "ERROR":
            error_info = response_data.get("error", {})
            cause = error_info.get('cause', 'Unknown cause')
            explanation = error_info.get('explanation', 'No explanation provided')
            field = error_info.get('field', 'Unknown field')
            validation_type = error_info.get('validationType', 'Unknown validation type')
            # Raise detailed error message
            raise ValueError(
                f"Failed to initiate checkout session:\n"
                f"Cause: {cause}\n"
                f"Explanation: {explanation}\n"
                f"Missing Parameter: {field}\n"
                f"Validation Type: {validation_type}"
            )
        session_id = response_data.get("session", {}).get("id")
        success_indicator = response_data.get("successIndicator")
        # Save transaction info
        tx.write({
            # str(tx.id) + '' + tx.reference
            'provider_reference': f"{tx.id}{tx.reference}",
            'mpgs_Indicator': success_indicator,
        })
        res['session_id'] = session_id
        # res['session_version'] = response_data.get("session", {}).get("version")
        return res

    def _process_notification_data(self, data):
        """ Override of payment to process the transaction based on data.

        Note: self.ensure_one()

        :param dict data: The feedback data
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(data)
        if self.provider_code != "mpgs":
            return
        # if not self._context.get('mobikul_mpgs'):
        self._set_done()
        # self.with_context({'mpgs': True})._reconcile_after_done()

    # def _reconcile_after_done(self):
    #     """ Override of payment to automatically confirm quotations and generate invoices. """
    #     if self._context.get('mpgs'):
    #         if self.operation == 'refund':
    #             self._create_payment()
    #         else:
    #             sales_orders = self.mapped('sale_order_ids').filtered(lambda so: so.state in ('draft', 'sent'))
    #             for tx in self:
    #                 tx._check_amount_and_confirm_order()
    #             # send order confirmation mail
    #             # sales_orders._send_order_confirmation_mail()
    #             # invoice the sale orders if needed
    #             self._invoice_sale_orders()
    #             if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice') and any(
    #                     so.state in ('sale', 'dispatch', 'done') for so in self.sale_order_ids):
    #                 default_template = self.env['ir.config_parameter'].sudo().get_param(
    #                     'sale.default_invoice_email_template')
    #                 if default_template:
    #                     for trans in self.filtered(
    #                             lambda t: t.sale_order_ids.filtered(
    #                                 lambda so: so.state in ('sale', 'dispatch', 'done'))):
    #                         trans = trans.with_company(trans.provider_id.company_id).with_context(
    #                             mark_invoice_as_sent=True,
    #                             company_id=trans.provider_id.company_id,
    #                         )
    #                         # for invoice in trans.invoice_ids.with_user(SUPERUSER_ID):
    #                         #     invoice.message_post_with_template(int(default_template),
    #                         #                                        email_layout_xmlid="mail.mail_notification_paynow")
    #                 self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()

    #                 # Create and post missing payments for transactions requiring reconciliation
    #                 for tx in self.filtered(lambda t: t.operation != 'validation' and not t.payment_id):
    #                     tx._create_payment()
    #     else:
    #         return super()._reconcile_after_done()

    def get_transaction_id(self):
        """
        Use: return unique string
        """
        return ''.join(random.choice(string.digits) for i in range(40))

    def _send_refund_request(self, amount_to_refund=None, create_refund_transaction=True):
        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        if self.provider_code != 'mpgs':
            return refund_tx

        transaction_id = self.get_transaction_id()
        order_id = f"{self.id}"
        merchant_id = self.provider_id.merchant_id

        mpgs_request_url = 'https://banquemisr.gateway.mastercard.com/api/rest/version/100/merchant/%s/order/%s/transaction/%s' % (
            merchant_id, order_id, transaction_id)
        json = {"apiOperation": "REFUND",
                "transaction": {"amount": amount_to_refund, "currency": refund_tx.currency_id.name},
                }
        request_url = requests.put(mpgs_request_url,
                                   auth=('merchant.' + self.provider_id.merchant_id, self.provider_id.mpgs_secret_key),
                                   json=json, timeout=30)

        response_content = request_url.json()

        if response_content["result"] == "SUCCESS" or response_content.get('response', False) and \
                response_content["response"]["gatewayCode"] == 'APPROVED':
            refund_tx._process_notification_data(response_content)

        else:
            if response_content.get("result") == 'ERROR':
                raise UserError(_(response_content['error']['explanation']))

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of `payment` to find the transaction based on APS data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data are received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if self._context.get('from_webhook'):
            id = int(notification_data.get('transaction', {}).get('acquirer', {}).get('transactionId'))
            tx = self.search([('id', '=', id), ('provider_code', '=', 'mpgs')])
        else:
            if provider_code != 'mpgs' or len(tx) == 1:
                return tx

            reference = notification_data.get('resultIndicator')
            if not reference:
                raise ValidationError(
                    "MPGS: " + _("Received data with missing resultIndicator %(ref)s.", ref=reference)
                )

            tx = self.search([('mpgs_Indicator', '=', reference), ('provider_code', '=', 'mpgs')])
            if not tx:
                raise ValidationError(
                    "MPGS: " + _("No transaction found matching resultIndicator %s.", reference)
                )

        return tx
