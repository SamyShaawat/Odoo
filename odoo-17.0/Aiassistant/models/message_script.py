from odoo import api, fields, models


class WhatsappScriptMessage(models.Model):
    _name = "whatsapp.message.script.message"
    _rec_name = 'message'

    message = fields.Char('Message')


class WhatsappScript(models.Model):
    _name = "whatsapp.message.script"
    _rec_name= 'name'

    name = fields.Char(string="Name")
    messages = fields.Many2many('whatsapp.message.script.message')
