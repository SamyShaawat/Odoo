
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
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons.aspl_payment_mpgs_ee_webhook.const import APPROVED_TRANSACTION_GATEWAY_CODES

_logger = logging.getLogger(__name__)

class PaymentTxmpgs(models.Model):
    _inherit = 'payment.transaction'


    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Mpgs data.

                     Note: self.ensure_one()

                     :param dict data: The notification data sent by the provider
                     :return: None
                     :raise: ValidationError if inconsistent data were received
                     """
        if self._context.get('from_webhook'):
            if self.provider_code != 'mpgs':
                return

            if notification_data.get("result") == "SUCCESS" and notification_data.get("response", {}).get(
                    "gatewayCode") in APPROVED_TRANSACTION_GATEWAY_CODES:
                self._set_done()
            elif notification_data.get("result") == "PENDING" and notification_data.get("response", {}).get(
                    "gatewayCode") == 'PENDING':
                self._set_pending()
            else:
                self._set_canceled()
                _logger.info(
                    "received data with payment status (%s) for transaction with reference %s",
                    notification_data.get("response", {}).get("gatewayCode"), self.reference,
                )
                self._set_error(
                    "MPGS: " + _("transaction Failed: %s", notification_data.get("response", {}).get("gatewayCode")))
        else:
            super()._process_notification_data(notification_data)