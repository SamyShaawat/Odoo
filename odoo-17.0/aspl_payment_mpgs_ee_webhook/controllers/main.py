import pprint
import logging
import hmac

from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.api import Environment, SUPERUSER_ID
from werkzeug.exceptions import Forbidden
import json

_logger = logging.getLogger(__name__)


class MpgsWebHook(WebsiteSale):
    webhook_url = '/payment/mpgs/webhook'

    @http.route(webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def mpgs_webhook(self, **data):
        """ Process the notification data sent by MPGS to the webhook.

        See https://paymentservices-reference.payfort.com/docs/api/build/index.html#transaction-feedback.

        :param dict data: The notification data.
        :return: The 'SUCCESS' string to acknowledge the notification
        :rtype: str
        """
        data = json.loads(request.httprequest.data)
        _logger.info("Notification received from MPGS with data:\n%s", pprint.pformat(data))
        env = Environment(request.env.cr, SUPERUSER_ID, {})
        mpgs = env.ref("aspl_payment_mpgs_ee.payment_acquirer_mpgs")
        secret_configured = mpgs.mpgs_notification_secret
        _logger.info("secret configured {}".format(secret_configured))

        if not secret_configured:
            # Notification secret is not configured
            _logger.warning("MPGS : Notification secret is not configured")
            return request.make_json_response(
                {"ok": False},
                status=400
            )

        if secret_configured != request.httprequest.headers.get("X-Notification-Secret"):
            # Incorrect secret configured
            _logger.warning("incorrect secret given {}".format(secret_configured != request.httprequest.headers.get("X-Notification-Secret")))
            return request.make_json_response(
                {"ok": False},
                status=400
            )

        if data.get('order', {}).get('totalCapturedAmount') > 0:
            try:
                # Check the integrity of the notification.
                tx_sudo = request.env['payment.transaction'].sudo().with_context(from_webhook=True)._get_tx_from_notification_data(
                    'mpgs', data
                )
                # self._verify_notification_signature(data, tx_sudo)

                # Handle the notification data.
                tx_sudo._handle_notification_data('mpgs', data)
            except ValidationError:  # Acknowledge the notification to avoid getting spammed.
                _logger.exception("Unable to handle the notification data; skipping to acknowledge.")

            return request.make_json_response(
                {"ok": True},
                status=200
            )
  # Acknowledge the notification.


    # @staticmethod
    # def _verify_notification_signature(notification_data, tx_sudo):
    #     """ Check that the received signature matches the expected one.
    #
    #     :param dict notification_data: The notification data
    #     :param recordset tx_sudo: The sudoed transaction referenced by the notification data, as a
    #                               `payment.transaction` record
    #     :return: None
    #     :raise: :class:`werkzeug.exceptions.Forbidden` if the signatures don't match
    #     """
    #     received_signature = notification_data.get('resultIndicator')
    #     if not received_signature:
    #         _logger.warning("received notification with missing signature")
    #         raise Forbidden()
    #
    #     # Compare the received signature with the expected signature computed from the data.
    #     expected_signature = tx_sudo.mpgs_Indicator
    #     if not hmac.compare_digest(received_signature, expected_signature):
    #         _logger.warning("received notification with invalid signature")
    #         raise Forbidden()