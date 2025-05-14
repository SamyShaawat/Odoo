from odoo import api, fields, models
import json


class Appointment(models.Model):
    _name = 'appointment.model'
    _description = 'Appointment'
    rec_name = "p_whatsapp_number"

    patient_id = fields.Many2one(comodel_name="patient.model", string="Patient", required=False, )
    doctor_id = fields.Many2one(comodel_name="doctor.model", string="Doctor", required=False, )
    clinic_id = fields.Many2one(comodel_name="clinic.model", string="clinic", required=False,
                                group_expand='_group_expand_clinic')
    appointment_date = fields.Date(string='Appointment Date')
    p_whatsapp_number = fields.Char(string='patient whatsapp Number')
    d_whatsapp_number = fields.Char(string='doctor whatsapp Number')
    domain = fields.Char(string="domain", compute="get_domain")
    appoint_state = fields.Selection(
        [('new', 'New'), ('inprogress', 'Inprogress'), ('vip', 'VIP'), ('emergency', 'Emergency'), ('done', 'Done')],
        string="State", default="new", track_visibility="onchange")

    @api.onchange('clinic_id')
    def get_domain(self):
        for rec in self:
            if self.clinic_id.assigned_to:
                rec.domain = json.dumps([('id', 'in', self.clinic_id.assigned_to.ids)])
            else:
                rec.domain = json.dumps([('id', 'in', [])])

    def _group_expand_clinic(self, states, domain, order):
        clinics = self.env['clinic.model'].search([])
        return clinics
