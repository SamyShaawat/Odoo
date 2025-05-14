from odoo import models, fields
from odoo.addons.asterisk_plus.models.server import SIP_TRANSPORT_SELECTION


class SetChannelTransportWizard(models.TransientModel):
    _name = 'asterisk_plus.set_channel_transport_wizard'
    _description = 'Set Channel Transport'

    transport = fields.Selection(SIP_TRANSPORT_SELECTION, required=True, default='webrtc-user')

    def submit(self):
        users = self.env['asterisk_plus.user'].browse(
            self.env.context['active_ids'])
        for user in users:
            user.channels.sip_transport = self.transport
