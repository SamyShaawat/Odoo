



# https://ap-gateway.mastercard.com/api/documentation/apiDocumentation/rest-json/version/latest/operation/Transaction%3a%20%20Capture.html?locale=en_US
APPROVED_TRANSACTION_GATEWAY_CODES = (
    "APPROVED",  # Transaction Approved
    "APPROVED_AUTO",  # The transaction was automatically approved by the gateway. it was not submitted to the acquirer.
    "APPROVED_PENDING_SETTLEMENT",  # Transaction Approved - pending batch settlement
)