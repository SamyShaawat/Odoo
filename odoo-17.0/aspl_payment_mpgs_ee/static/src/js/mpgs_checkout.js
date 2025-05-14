odoo.define('aspl_payment_mpgs_ee.mpgs_checkout', [
    '@web/core/l10n/translation',
    '@payment/js/payment_form',
    '@web/core/network/rpc_service'
], function(require) {

    'use strict';

    const _t = require('@web/core/l10n/translation');
    const paymentForm = require('@payment/js/payment_form');
    const jsonrpc = require('@web/core/network/rpc_service');

    $(document).ready(function() {
        // Log start for debugging
        console.log("Initializing MPGS checkout configuration...");

        // Retrieve values from hidden input fields
        const merchantId = $('#merchant_id').val();
        const amount = $('#amount').val();
        const currency = $('#currency').val();
        const orderId = $('#order_id').val();
        const customerEmail = $('#customer_email').val();
        const customerPhone = $('#customer_phone').val();
        const billingStreet = $('#billing_street').val();
        const billingCity = $('#billing_city').val();
        const billingZip = $('#billing_zip').val();
        const billingState = $('#billing_state').val();
        const billingCountry = $('#billing_country').val();
        const sessionId = $('#session_id').val();
        const sessionVersion = $('#session_version').val();

        // Log retrieved values for debugging
        console.log("Merchant ID:", merchantId);
        console.log("Session Version:", sessionVersion);

        // Check if essential values are present
        if (!merchantId || !sessionId || !sessionVersion) {
            console.error("Required payment details are missing. Please check the template and input fields.");
            return;
        }

        // Configure MPGS Checkout with extracted values
        Checkout.configure({
            merchant: merchantId,
            order: {
                amount: amount,
                currency: currency,
                description: "Order Payment",
                id: orderId,
            },
            billing: {
                address: {
                    street: billingStreet,
                    city: billingCity,
                    postcodeZip: billingZip,
                    stateProvince: billingState,
                    country: billingCountry,
                }
            },
            customer: {
                email: customerEmail,
                phone: customerPhone
            },
            session: {
                id: sessionId,
                version: sessionVersion
            }
        });

        // Display the MPGS payment page after a short delay
        setTimeout(function() {
            try {
                Checkout.showPaymentPage();
                console.log("Payment page displayed.");
            } catch (error) {
                console.error("Error displaying payment page:", error);
            }
        }, 1000);
    });
});
