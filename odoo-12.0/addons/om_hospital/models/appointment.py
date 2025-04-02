# -*- coding: utf-8 -*-

import pytz
from lxml import etree
from odoo import models, fields, api, _


class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _description = "Appointment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "appointment_date desc"

    # Overriding the Create Method in Odoo
    @api.model
    def create(self, vals):
        # overriding the create method to add the sequence
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "hospital.appointment"
            ) or _("New")
        result = super(HospitalAppointment, self).create(vals)
        return result

    # How To Set Default Value For The Field in Odoo12
    def _get_default_note(self):
        # res = super(HospitalAppointment, self).default_get(fields)
        # print("test......")
        # res["patient_id"] = 1
        # res["notes"] = "please like the video"
        # return "This is a default Note for Registration you can change it as you want"
        return 1

    name = fields.Char(
        string="Appointment ID",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )

    patient_id = fields.Many2one(
        "hospital.patient", string="Patient", required=True, default=_get_default_note
    )
    patient_age = fields.Integer("Age", related="patient_id.patient_age")
    notes = fields.Text(string="Registration Note")
    appointment_date = fields.Date(string="Date", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        default="draft",
    )
