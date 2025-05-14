from odoo import models, fields, api, _


class Clinic(models.Model):
    _name = 'clinic.model'
    _rec_name = 'name'
    _description = 'Clinics in cleopatra Hospitals'

    name = fields.Char(string="Clinic Name")
    assigned_to = fields.Many2many(comodel_name="doctor.model", relation="clinic_id", string="Assigned To", )
