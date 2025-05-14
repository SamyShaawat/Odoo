/** @odoo-module **/

import { Component } from '@odoo/owl';
import publicWidget from '@web/legacy/js/public/public_widget';
import PaymentForm from '@payment/js/payment_form'; // Assuming the original file path is 'web.payment_form'

const CustomPaymentForm = PaymentForm.extend({
    /**
     * Override the _processRedirectFlow method to provide custom logic.
     *
     * @private
     * @param {string} providerCode
     * @param {number} paymentOptionId
     * @param {string} paymentMethodCode
     * @param {object} processingValues
     */
    _processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        // Custom logic to append the redirect form to the body and submit it
        const $redirectForm = $(processingValues.redirect_form_html).attr('id', 'custom_payment_redirect_form');
        $(document.getElementsByTagName('body')[0]).append($redirectForm);

        // Submit the form
        $redirectForm.submit();
    },
});

// Register the extended widget
publicWidget.registry.PaymentForm = CustomPaymentForm;
