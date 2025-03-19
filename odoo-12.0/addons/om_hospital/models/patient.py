# -*- coding: utf-8 -*-

from odoo import models, fields
class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Patient Record'

    # patient_name = fields.Char(string='Name', required=True)
    # patient_age = fields.Integer('Age')
    # notes = fields.Text(string="Notes")
    # image = fields.Binary(string="Image")



