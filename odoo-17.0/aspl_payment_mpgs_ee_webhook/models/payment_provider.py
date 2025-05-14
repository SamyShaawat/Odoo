
from odoo import fields, models
class AcquirerMasterCard(models.Model):
    _inherit = 'payment.provider'

    mpgs_notification_secret = fields.Char("MGPS Notification Secret", required_if_provider="mpgs")

