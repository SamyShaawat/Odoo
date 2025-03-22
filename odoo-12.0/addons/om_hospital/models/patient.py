# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Patient Record"
    _rec_name = "patient_name"

    patient_name = fields.Char(string="Name", required=True)
    patient_age = fields.Integer("Age")
    notes = fields.Text(string="Notes")
    image = fields.Binary(string="Image")
    name = fields.Char(string="Test")
    name_seq = fields.Char(
        string="Patient ID",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )

    # Overriding the create method to assign sequence for the record
    @api.model
    def create(self, vals):
        if vals.get("name_seq", _("New")) == _("New"):
            vals["name_seq"] = self.env["ir.sequence"].next_by_code(
                "hospital.patient.sequence"
            ) or _("New")
        result = super(HospitalPatient, self).create(vals)
        return result
