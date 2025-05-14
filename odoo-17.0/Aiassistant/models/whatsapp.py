from odoo import models, fields, api, _
import json
import requests

class WhatsappProfile(models.Model):
    _name = 'whatsapp.profile'

    patient_name_id = fields.Many2one(comodel_name="patient.model", string="Patient Name")
    patient_whatsapp = fields.Char(string="Whatsapp number")
    whats_app = fields.One2many('whatsapp.msg', 'p_id', string="WhatsApp")
    clinic_id = fields.Many2one(comodel_name="clinic.model", string="Clinic", group_expand='_group_expand_clinic')
    script = fields.Many2one('whatsapp.message.script',string='Script')
    message_script = fields.Many2one('whatsapp.message.script.message',string='Scripted Message')
    domain_script = fields.Char(compute='domain_script_func')
    char_message = fields.Char(string='Message')
    last_message = fields.Char(string="last message", compute='get_last_mess')
    message_box = fields.Text(string="Message BOX")

    def _group_expand_clinic(self, states, domain, order):
        clinics = self.env['clinic.model'].search([])
        return clinics

    def send_message(self):
        for rec in self:
            token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJBUEkiLCJhcHAiOiI2NDU4YTRkZTlhMGU0YTU5ZDA3YzdlNjYiLCJhY2wiOlsiYXBpOmFkbWluIiwiYWNjb3VudDp1cGRhdGUiLCJhY3Rpb246Y3JlYXRlIiwiYWN0aW9uOmRlbGV0ZSIsImFjdGlvbjp1cGRhdGUiLCJhZ2VuZGE6Y3JlYXRlIiwiYWdlbmRhOmRlbGV0ZSIsImFnZW5kYTpyZWFkIiwiYWdlbmRhOnVwZGF0ZSIsImFwcDpsaW5rUGFydG5lciIsImFwcDpsaXN0TWFuYWdtZW50UmVxdWVzdCIsImFwcEluZm86Z2V0IiwiYXBwSW50ZWdyYXRpb246Y3JlYXRlIiwiYXBwSW50ZWdyYXRpb246ZGVsZXRlIiwid2hhdHNhcHA6Z2V0RmlsZSIsIndoYXRzYXBwTWVzc2FnZVRlbXBsYXRlczpjcmVhdGUiLCJ3aGF0c2FwcE1lc3NhZ2VUZW1wbGF0ZXM6ZGVsZXRlIiwid2hhdHNhcHBNZXNzYWdlVGVtcGxhdGVzOmdldCIsIndoYXRzYXBwTWVzc2FnZVRlbXBsYXRlczpsaXN0IiwidHJpZ2dlcjp1cGRhdGUiLCJ0cmlnZ2VyOmRlbGV0ZSIsInRyaWdnZXI6Y3JlYXRlIiwidHJlZTp1cGRhdGVUcmVlU2V0dGluZyIsInRyZWU6dXBkYXRlTm9kZXMiLCJ0cmVlOnVwZGF0ZUJhc2ljSW5mbyIsInRyZWU6cmVhZCIsInRyZWU6bGlzdCIsInRyZWU6aW1wb3J0IiwidHJlZTpnZXROb2RlcyIsInRyZWU6Z2V0VHJlZVNldHRpbmciLCJ0cmVlOmdldEJhc2ljSW5mbyIsInRyZWU6ZXhwb3J0IiwidHJlZTpkZWxldGUiLCJ0ZWFtTWVtYmVyOnVwZGF0ZSIsInRlYW1NZW1iZXI6bGlzdCIsInRlYW1NZW1iZXI6ZGVsZXRlIiwidGVhbU1lbWJlcjpjcmVhdGUiLCJyb2xlOmxpc3QiLCJyZXNwb25zZTp1cGRhdGUiLCJyZXNwb25zZTpkZWxldGUiLCJyZXNwb25zZTpjcmVhdGUiLCJub2RlOnVwZGF0ZSIsInByaW9yaXR5R3JvdXA6Y3JlYXRlIiwicHJpb3JpdHlHcm91cDpkZWxldGUiLCJwcmlvcml0eUdyb3VwOmdldCIsInByaW9yaXR5R3JvdXA6bGlzdCIsInByaW9yaXR5R3JvdXA6dXBkYXRlIiwicHVzaDpjcmVhdGUiLCJwdXNoOmRlbGV0ZSIsInB1c2g6Z2V0IiwicHVzaDpsaXN0IiwicHVzaDp1cGRhdGUiLCJub2RlOmRlbGV0ZSIsIm5vZGU6Y3JlYXRlIiwibWVtYmVyczptYW5hZ2VUYWdzIiwibWVtYmVyVGFnczpnZXQiLCJtZW1iZXJUYWdzOmRlbGV0ZSIsIm1lbWJlclRhZ3M6Y3JlYXRlIiwibWVtYmVyOndyaXRlIiwibWVtYmVyOnVwZGF0ZURldGFpbHMiLCJtZW1iZXI6cmVhZCIsIm1lZGlhTGlicmFyeTp1cGRhdGUiLCJtZW1iZXI6VG9nZ2xlTGl2ZUNoYXQiLCJtZW1iZXI6YWRtaW4iLCJtZW1iZXI6Y3JlYXRlIiwibWVtYmVyOmRlbGV0ZSIsIm1lbWJlcjpleHBvcnQiLCJtZW1iZXI6Z2V0Q29udmVyc2F0aW9uIiwibWVtYmVyOmdldERldGFpbHMiLCJtZW1iZXI6aW1wb3J0IiwibWVtYmVyOmxpc3QiLCJtZWRpYUxpYnJhcnk6bGlzdCIsIm1lZGlhTGlicmFyeTpnZXQiLCJtZWRpYUxpYnJhcnk6ZGVsZXRlIiwibWVkaWFMaWJyYXJ5OmNyZWF0ZSIsImxvZzpsaXN0IiwiaW50ZWdyYXRpb246dXBkYXRlIiwiaW50ZWdyYXRpb246bGlzdCIsImludGVncmF0aW9uOmdldCIsImludGVncmF0aW9uOmNyZWF0ZSIsImZpbGU6d2FHZXQiLCJmaWxlOmdldCIsImZpbGU6YWRtaW4iLCJkYXRhU291cmNlOnVwZGF0ZURvYyIsImRhdGFTb3VyY2U6dXBkYXRlRGF0YXNvdXJjZSIsImRhdGFTb3VyY2U6bGlzdERvY3MiLCJkYXRhU291cmNlOmxpc3REYXRhc291cmNlcyIsImRhdGFTb3VyY2U6aW1wb3J0RGF0YXNvdXJjZSIsImRhdGFTb3VyY2U6Z2V0RG9jIiwiZGF0YVNvdXJjZTpleHBvcnREYXRhc291cmNlIiwiZGF0YVNvdXJjZTpkZWxldGVEb2MiLCJkYXRhU291cmNlOmRlbGV0ZURhdGFzb3VyY2UiLCJkYXRhU291cmNlOmNyZWF0ZURvYyIsImRhdGFTb3VyY2U6Y3JlYXRlRGF0YXNvdXJjZSIsImRhc2hib2FyZDpsaXN0V2hhdHNhcHBBbmFseXRpY3MiLCJkYXNoYm9hcmQ6bGlzdFVzZXJzIiwiZGFzaGJvYXJkOmxpc3RUaWNrZXRpbmciLCJkYXNoYm9hcmQ6bGlzdE5scEFuYWx5dGljcyIsImRhc2hib2FyZDpsaXN0Q29tbWVudFJlcGx5IiwiZGFzaGJvYXJkOmxpc3RBc3NpZ25tZW50IiwiY2hhbm5lbDp1cGRhdGVUcmVlU2V0dGluZ3MiLCJjaGF0OmV4cG9ydCIsImNvbmRpdGlvbjpjcmVhdGUiLCJjb25kaXRpb246ZGVsZXRlIiwiY29uZGl0aW9uOnVwZGF0ZSIsImNvbnZlcnNhdGlvbjpyZWFkIiwiZGFzaGJvYXJkOmV4cG9ydEFuYWx5dGljcyIsImRhc2hib2FyZDpleHBvcnRVc2VycyIsImRhc2hib2FyZDpsaXN0QWdlbnRzIiwiZGFzaGJvYXJkOmxpc3RBbmFseXRpY3MiLCJjaGFubmVsOnVwZGF0ZVBsYXRmb3JtU2V0dGluZ3MiLCJjaGFubmVsOnVwZGF0ZVBsYXRmb3JtSW5mbyIsImNoYW5uZWw6dXBkYXRlTGl2ZUNoYXRTZXR0aW5ncyIsImNoYW5uZWw6dXBkYXRlRW52aXJvbm1lbnRJbmZvIiwiY2hhbm5lbDp1cGRhdGVEZXRhaWwiLCJjaGFubmVsOnVwZGF0ZUJyb2FkY2FzdEdyb3VwU2V0dGluZ3MiLCJjaGFubmVsOnVwZGF0ZUJhc2ljSW5mbyIsImNoYW5uZWw6dXBkYXRlQXZhaWxhYmlsaXRpZXMiLCJjaGFubmVsOmxpc3QiLCJjaGFubmVsOmdldFRyZWVTZXR0aW5ncyIsImNoYW5uZWw6Z2V0UGxhdGZvcm1TZXR0aW5ncyIsImNoYW5uZWw6Z2V0UGxhdGZvcm1JbmZvIiwiY2hhbm5lbDpnZXRMaXZlQ2hhdFNldHRpbmdzIiwiY2hhbm5lbDpkZWxldGVFbnZpcm9ubWVudCIsImNoYW5uZWw6Z2V0QXZhaWxhYmlsaXRpZXMiLCJjaGFubmVsOmdldEJhc2ljSW5mbyIsImNoYW5uZWw6Z2V0QnJvYWRjYXN0R3JvdXBTZXR0aW5ncyIsImNoYW5uZWw6Z2V0RGV0YWlscyIsImNoYW5uZWw6Z2V0RW52aXJvbm1lbnRJbmZvIiwiY2hhbm5lbDpjcmVhdGVDaGFubmVsIiwiY2hhbm5lbDpjcmVhdGVFbnZpcm9ubWVudCIsImNoYW5uZWw6ZGVsZXRlQ2hhbm5lbCIsImJvdGJ1aWxkZXI6cmVhZCIsImJvdGJ1aWxkZXI6bWFuYWdlIiwiYm90OnNlbmRSZXNwb25zZXMiLCJib3Q6cmVkaXJlY3RNZW1iZXJUb05vZGUiLCJib3Q6YWRtaW4iLCJhdWRpdFRyYWlsOmxpc3QiLCJiYWNrZ3JvdW5kVGFzazpnZXQiLCJiYWNrZ3JvdW5kVGFzazpsaXN0IiwiYmlsbGluZzpjcmVhdGVTdWJzY3JpcHRpb24iLCJiaWxsaW5nOmRlbGV0ZVN1YnNjcmlwdGlvbiIsImJpbGxpbmc6Z2V0U3Vic2NyaXB0aW9uIiwiYmlsbGluZzpsaXN0SW52b2ljZXMiLCJiaWxsaW5nOnVwZGF0ZVN1YnNjcmlwdGlvbiIsImF1ZGllbmNlOnVwZGF0ZSIsImF1ZGllbmNlOnJlYWQiLCJhdWRpZW5jZTpsaXN0IiwiYXVkaWVuY2U6Z2V0IiwiYXVkaWVuY2U6ZGVsZXRlIiwiYXVkaWVuY2U6Y3JlYXRlIiwiYXR0YWNobWVudElkOmxpc3QiLCJhcHBJbnRlZ3JhdGlvbjpnZXQiLCJhcHBJbnRlZ3JhdGlvbjpsaXN0IiwiYXBwSW50ZWdyYXRpb246dXBkYXRlIiwiYXBwU2V0dGluZ3M6Z2V0IiwiYXBwU2V0dGluZ3M6dXBkYXRlIiwiYXNzaWdubWVudDpsaXN0IiwiYXR0YWNobWVudElkOmNyZWF0ZSJdLCJqdGkiOiIwNDJiZDUxNC0zOTkyLTVmMmEtOTY2NS0wNGU4NTUwYzQ5MmQiLCJpc3MiOiI2NDU4YTRhZTNiZWIwMTAxMjcwOWI3ZjIiLCJpYXQiOjE2ODQwNjYxMDYyMzh9.Kip5h5leVtDojhakyroL2Rh9lzBt7QF-KCSuov9zhIo'
            url = "https://bot.api.woztell.com/sendResponses?accessToken=" + token
            channel_id = '645bf628d76ad166d9fae864'
            if rec.message_box:
                response = {
                    "channelId": channel_id,
                    "recipientId": rec.patient_whatsapp,
                    "response": [
                        {
                            "type": "TEXT",
                            "text": rec.message_box
                        }
                    ]
                }
                requests.post(url, json=response)
                rec.write({
                    'whats_app': [(0, 0, {
                        'receiver': rec.message_box,
                    })]
                })
            elif rec.message_script:
                response = {
                    "channelId": channel_id,
                    "recipientId": rec.patient_whatsapp,
                    "response": [
                        {
                            "type": "TEXT",
                            "text": rec.message_script.message
                        }
                    ]
                }
                requests.post(url, json=response)
                rec.write({
                    'whats_app': [(0, 0, {
                        'receiver': rec.message_script.message,
                    })]
                })


    @api.onchange('script')
    def domain_script_func(self):
        for rec in self:
            if rec.script:
                rec.domain_script = json.dumps([('id', 'in', rec.script.messages.ids)])
            else:
                rec.domain_script = json.dumps([])


    @api.onchange("whats_app")
    def get_last_mess(self):
        for rec in self:
            if rec.whats_app:
                rec.last_message = rec.whats_app[-1].sender

    def action_send_msg(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Whatsapp Message'),
                'res_model': 'whatsapp.send.message',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_profile_id': self.id}}


class Messages(models.Model):
    _name = "whatsapp.msg"

    sender = fields.Char(string="Message sent")
    receiver = fields.Char(string="Message received")
    p_id = fields.Many2one('whatsapp.profile', string='Profile')
