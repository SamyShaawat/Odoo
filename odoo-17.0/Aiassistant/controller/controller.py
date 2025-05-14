from odoo import fields
from odoo import http
from odoo.http import request
import requests
from datetime import datetime
import yaml

class WhatsappWoztell(http.Controller):
    @http.route('/whatsapp/integration', type='json', auth='public', methods=['GET','POST'], csrf=False)
    def handle_webhook(self, **kw):
        uid = request.session.authenticate('Agial_Test', 'admin@agial.com', 'P@ssw0rd_P@ssw0rd')
        print('-------------------------------------------data--------------------------------------------')
        # data = request.jsonrequest
        requested_data = request.httprequest.data
        data = yaml.safe_load(requested_data)
        
        print(data)
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJBUEkiLCJhcHAiOiI2NDU4YTRkZTlhMGU0YTU5ZDA3YzdlNjYiLCJhY2wiOlsiYXBpOmFkbWluIiwiYWNjb3VudDp1cGRhdGUiLCJhY3Rpb246Y3JlYXRlIiwiYWN0aW9uOmRlbGV0ZSIsImFjdGlvbjp1cGRhdGUiLCJhZ2VuZGE6Y3JlYXRlIiwiYWdlbmRhOmRlbGV0ZSIsImFnZW5kYTpyZWFkIiwiYWdlbmRhOnVwZGF0ZSIsImFwcDpsaW5rUGFydG5lciIsImFwcDpsaXN0TWFuYWdtZW50UmVxdWVzdCIsImFwcEluZm86Z2V0IiwiYXBwSW50ZWdyYXRpb246Y3JlYXRlIiwiYXBwSW50ZWdyYXRpb246ZGVsZXRlIiwid2hhdHNhcHA6Z2V0RmlsZSIsIndoYXRzYXBwTWVzc2FnZVRlbXBsYXRlczpjcmVhdGUiLCJ3aGF0c2FwcE1lc3NhZ2VUZW1wbGF0ZXM6ZGVsZXRlIiwid2hhdHNhcHBNZXNzYWdlVGVtcGxhdGVzOmdldCIsIndoYXRzYXBwTWVzc2FnZVRlbXBsYXRlczpsaXN0IiwidHJpZ2dlcjp1cGRhdGUiLCJ0cmlnZ2VyOmRlbGV0ZSIsInRyaWdnZXI6Y3JlYXRlIiwidHJlZTp1cGRhdGVUcmVlU2V0dGluZyIsInRyZWU6dXBkYXRlTm9kZXMiLCJ0cmVlOnVwZGF0ZUJhc2ljSW5mbyIsInRyZWU6cmVhZCIsInRyZWU6bGlzdCIsInRyZWU6aW1wb3J0IiwidHJlZTpnZXROb2RlcyIsInRyZWU6Z2V0VHJlZVNldHRpbmciLCJ0cmVlOmdldEJhc2ljSW5mbyIsInRyZWU6ZXhwb3J0IiwidHJlZTpkZWxldGUiLCJ0ZWFtTWVtYmVyOnVwZGF0ZSIsInRlYW1NZW1iZXI6bGlzdCIsInRlYW1NZW1iZXI6ZGVsZXRlIiwidGVhbU1lbWJlcjpjcmVhdGUiLCJyb2xlOmxpc3QiLCJyZXNwb25zZTp1cGRhdGUiLCJyZXNwb25zZTpkZWxldGUiLCJyZXNwb25zZTpjcmVhdGUiLCJub2RlOnVwZGF0ZSIsInByaW9yaXR5R3JvdXA6Y3JlYXRlIiwicHJpb3JpdHlHcm91cDpkZWxldGUiLCJwcmlvcml0eUdyb3VwOmdldCIsInByaW9yaXR5R3JvdXA6bGlzdCIsInByaW9yaXR5R3JvdXA6dXBkYXRlIiwicHVzaDpjcmVhdGUiLCJwdXNoOmRlbGV0ZSIsInB1c2g6Z2V0IiwicHVzaDpsaXN0IiwicHVzaDp1cGRhdGUiLCJub2RlOmRlbGV0ZSIsIm5vZGU6Y3JlYXRlIiwibWVtYmVyczptYW5hZ2VUYWdzIiwibWVtYmVyVGFnczpnZXQiLCJtZW1iZXJUYWdzOmRlbGV0ZSIsIm1lbWJlclRhZ3M6Y3JlYXRlIiwibWVtYmVyOndyaXRlIiwibWVtYmVyOnVwZGF0ZURldGFpbHMiLCJtZW1iZXI6cmVhZCIsIm1lZGlhTGlicmFyeTp1cGRhdGUiLCJtZW1iZXI6VG9nZ2xlTGl2ZUNoYXQiLCJtZW1iZXI6YWRtaW4iLCJtZW1iZXI6Y3JlYXRlIiwibWVtYmVyOmRlbGV0ZSIsIm1lbWJlcjpleHBvcnQiLCJtZW1iZXI6Z2V0Q29udmVyc2F0aW9uIiwibWVtYmVyOmdldERldGFpbHMiLCJtZW1iZXI6aW1wb3J0IiwibWVtYmVyOmxpc3QiLCJtZWRpYUxpYnJhcnk6bGlzdCIsIm1lZGlhTGlicmFyeTpnZXQiLCJtZWRpYUxpYnJhcnk6ZGVsZXRlIiwibWVkaWFMaWJyYXJ5OmNyZWF0ZSIsImxvZzpsaXN0IiwiaW50ZWdyYXRpb246dXBkYXRlIiwiaW50ZWdyYXRpb246bGlzdCIsImludGVncmF0aW9uOmdldCIsImludGVncmF0aW9uOmNyZWF0ZSIsImZpbGU6d2FHZXQiLCJmaWxlOmdldCIsImZpbGU6YWRtaW4iLCJkYXRhU291cmNlOnVwZGF0ZURvYyIsImRhdGFTb3VyY2U6dXBkYXRlRGF0YXNvdXJjZSIsImRhdGFTb3VyY2U6bGlzdERvY3MiLCJkYXRhU291cmNlOmxpc3REYXRhc291cmNlcyIsImRhdGFTb3VyY2U6aW1wb3J0RGF0YXNvdXJjZSIsImRhdGFTb3VyY2U6Z2V0RG9jIiwiZGF0YVNvdXJjZTpleHBvcnREYXRhc291cmNlIiwiZGF0YVNvdXJjZTpkZWxldGVEb2MiLCJkYXRhU291cmNlOmRlbGV0ZURhdGFzb3VyY2UiLCJkYXRhU291cmNlOmNyZWF0ZURvYyIsImRhdGFTb3VyY2U6Y3JlYXRlRGF0YXNvdXJjZSIsImRhc2hib2FyZDpsaXN0V2hhdHNhcHBBbmFseXRpY3MiLCJkYXNoYm9hcmQ6bGlzdFVzZXJzIiwiZGFzaGJvYXJkOmxpc3RUaWNrZXRpbmciLCJkYXNoYm9hcmQ6bGlzdE5scEFuYWx5dGljcyIsImRhc2hib2FyZDpsaXN0Q29tbWVudFJlcGx5IiwiZGFzaGJvYXJkOmxpc3RBc3NpZ25tZW50IiwiY2hhbm5lbDp1cGRhdGVUcmVlU2V0dGluZ3MiLCJjaGF0OmV4cG9ydCIsImNvbmRpdGlvbjpjcmVhdGUiLCJjb25kaXRpb246ZGVsZXRlIiwiY29uZGl0aW9uOnVwZGF0ZSIsImNvbnZlcnNhdGlvbjpyZWFkIiwiZGFzaGJvYXJkOmV4cG9ydEFuYWx5dGljcyIsImRhc2hib2FyZDpleHBvcnRVc2VycyIsImRhc2hib2FyZDpsaXN0QWdlbnRzIiwiZGFzaGJvYXJkOmxpc3RBbmFseXRpY3MiLCJjaGFubmVsOnVwZGF0ZVBsYXRmb3JtU2V0dGluZ3MiLCJjaGFubmVsOnVwZGF0ZVBsYXRmb3JtSW5mbyIsImNoYW5uZWw6dXBkYXRlTGl2ZUNoYXRTZXR0aW5ncyIsImNoYW5uZWw6dXBkYXRlRW52aXJvbm1lbnRJbmZvIiwiY2hhbm5lbDp1cGRhdGVEZXRhaWwiLCJjaGFubmVsOnVwZGF0ZUJyb2FkY2FzdEdyb3VwU2V0dGluZ3MiLCJjaGFubmVsOnVwZGF0ZUJhc2ljSW5mbyIsImNoYW5uZWw6dXBkYXRlQXZhaWxhYmlsaXRpZXMiLCJjaGFubmVsOmxpc3QiLCJjaGFubmVsOmdldFRyZWVTZXR0aW5ncyIsImNoYW5uZWw6Z2V0UGxhdGZvcm1TZXR0aW5ncyIsImNoYW5uZWw6Z2V0UGxhdGZvcm1JbmZvIiwiY2hhbm5lbDpnZXRMaXZlQ2hhdFNldHRpbmdzIiwiY2hhbm5lbDpkZWxldGVFbnZpcm9ubWVudCIsImNoYW5uZWw6Z2V0QXZhaWxhYmlsaXRpZXMiLCJjaGFubmVsOmdldEJhc2ljSW5mbyIsImNoYW5uZWw6Z2V0QnJvYWRjYXN0R3JvdXBTZXR0aW5ncyIsImNoYW5uZWw6Z2V0RGV0YWlscyIsImNoYW5uZWw6Z2V0RW52aXJvbm1lbnRJbmZvIiwiY2hhbm5lbDpjcmVhdGVDaGFubmVsIiwiY2hhbm5lbDpjcmVhdGVFbnZpcm9ubWVudCIsImNoYW5uZWw6ZGVsZXRlQ2hhbm5lbCIsImJvdGJ1aWxkZXI6cmVhZCIsImJvdGJ1aWxkZXI6bWFuYWdlIiwiYm90OnNlbmRSZXNwb25zZXMiLCJib3Q6cmVkaXJlY3RNZW1iZXJUb05vZGUiLCJib3Q6YWRtaW4iLCJhdWRpdFRyYWlsOmxpc3QiLCJiYWNrZ3JvdW5kVGFzazpnZXQiLCJiYWNrZ3JvdW5kVGFzazpsaXN0IiwiYmlsbGluZzpjcmVhdGVTdWJzY3JpcHRpb24iLCJiaWxsaW5nOmRlbGV0ZVN1YnNjcmlwdGlvbiIsImJpbGxpbmc6Z2V0U3Vic2NyaXB0aW9uIiwiYmlsbGluZzpsaXN0SW52b2ljZXMiLCJiaWxsaW5nOnVwZGF0ZVN1YnNjcmlwdGlvbiIsImF1ZGllbmNlOnVwZGF0ZSIsImF1ZGllbmNlOnJlYWQiLCJhdWRpZW5jZTpsaXN0IiwiYXVkaWVuY2U6Z2V0IiwiYXVkaWVuY2U6ZGVsZXRlIiwiYXVkaWVuY2U6Y3JlYXRlIiwiYXR0YWNobWVudElkOmxpc3QiLCJhcHBJbnRlZ3JhdGlvbjpnZXQiLCJhcHBJbnRlZ3JhdGlvbjpsaXN0IiwiYXBwSW50ZWdyYXRpb246dXBkYXRlIiwiYXBwU2V0dGluZ3M6Z2V0IiwiYXBwU2V0dGluZ3M6dXBkYXRlIiwiYXNzaWdubWVudDpsaXN0IiwiYXR0YWNobWVudElkOmNyZWF0ZSJdLCJqdGkiOiIwNDJiZDUxNC0zOTkyLTVmMmEtOTY2NS0wNGU4NTUwYzQ5MmQiLCJpc3MiOiI2NDU4YTRhZTNiZWIwMTAxMjcwOWI3ZjIiLCJpYXQiOjE2ODQwNjYxMDYyMzh9.Kip5h5leVtDojhakyroL2Rh9lzBt7QF-KCSuov9zhIo'
        url = "https://bot.api.woztell.com/sendResponses?accessToken=" + token
        channel_id = '645bf628d76ad166d9fae864'
        if data['type'] == 'TEXT' or data['type'] == 'PAYLOAD':
            x = request.env['whatsapp.profile'].search([('patient_whatsapp', '=', data['from'])], limit=1)
        if data['type'] == 'TEXT':
            if x:
                x.write({
                    'whats_app': [(0, 0, {
                        'sender': data['data']['text'],
                        'receiver': " ",
                    })]
                })
            else:
                request.env['whatsapp.profile'].create({
                    'patient_whatsapp': data['from'],
                    'whats_app': [(0, 0, {
                        'sender': data['data']['text'],
                        'receiver': " ",
                    })]
                })
        elif data['type'] == 'PAYLOAD':
            if x:
                x.write({
                    'whats_app': [(0, 0, {
                        'sender': data['data']['title'],
                        'receiver': " ",
                    })]
                })
                if data["data"]['payload'] == "Booking Appointment":
                    request.env['appointment.model'].create({
                        "appointment_date": datetime.now(),
                        'p_whatsapp_number': data['from']
                    })
                if data["data"]['payload'] == "Chest (Pulm. Disease)":
                    # check if there is an appointment or not
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)
                    if appointment:
                        appointment.write({
                            'clinic_id': 1
                        })
                        x.write({
                            'clinic_id': 1
                        })

                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 1
                        })
                elif data["data"]['payload'] == "Endocrine":
                    # check if there is an appointment or not
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 3
                        })
                        x.write({
                            'clinic_id': 3
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 3
                        })
                elif data["data"]['payload'] == "ENT":
                    # check if there is an appointment or not
                    print("YES")
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 4
                        })
                        x.write({
                            'clinic_id': 4
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 4
                        })
                elif data["data"]['payload'] == "Immunology & Hypersens.":
                    # check if there is an appointment or not
                    print("YES")
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 5
                        })
                        x.write({
                            'clinic_id': 5
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 5
                        })
                elif data["data"]['payload'] == "Internal medicine":
                    # check if there is an appointment or not
                    print("YES")
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 6
                        })
                        x.write({
                            'clinic_id': 6
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 6
                        })
                elif data["data"]['payload'] == "Obstetrics & Gynecology":
                    # check if there is an appointment or not
                    print("YES")
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 7
                        })
                        x.write({
                            'clinic_id': 7
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 7
                        })
                elif data["data"]['payload'] == "Ophthalmology":
                    # check if there is an appointment or not
                    print("YES")
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 8
                        })
                        x.write({
                            'clinic_id': 8
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 8
                        })
                elif data["data"]['payload'] == "Pediatrics":
                    # check if there is an appointment or not
                    print("YES")
                    appointment = request.env['appointment.model'].search([('p_whatsapp_number', '=', data['from'])],
                                                                          limit=1)

                    if appointment:
                        appointment.write({
                            'clinic_id': 9
                        })
                        x.write({
                            'clinic_id': 9
                        })
                    else:
                        request.env['appointment.model'].create({
                            "appointment_date": datetime.now(),
                            'p_whatsapp_number': data['from'],
                            'clinic_id': 9
                        })
            else:
                request.env['whatsapp.profile'].create({
                    'patient_whatsapp': data['from'],
                    'whats_app': [(0, 0, {
                        'sender': data['data']['title'],
                        'receiver': " ",
                    })]
                })
