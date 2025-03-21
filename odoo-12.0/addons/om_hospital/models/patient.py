# -*- coding: utf-8 -*-

from odoo import models, fields
class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Patient Record'
    _rec_name = 'patient_name'

    patient_name = fields.Char(string='Name', required=True)
    patient_age = fields.Integer('Age')
    notes = fields.Text(string="Notes")
    image = fields.Binary(string="Image")
    name = fields.Char(string="Test")




