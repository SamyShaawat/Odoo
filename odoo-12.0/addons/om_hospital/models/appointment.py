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

    # Moving the State Of the Record To Confirm State in Button Click
    # How to Add States/Statusbar for Records in Odoo
    def action_confirm(self):
        for record in self:
            record.state = "confirm"

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_reset_draft(self):
        for record in self:
            record.state = "draft"

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
    appointment_lines = fields.One2many(
        "hospital.appointment.lines", "appointment_id", string="Appointment Lines"
    )
    appointment_date = fields.Date(string="Date", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=False,
        tracking=True,
        default="draft",
    )


class HospitalAppointmentLines(models.Model):
    _name = "hospital.appointment.lines"
    _description = "Appointment Lines"

    product_id = fields.Many2one("product.product", string="Medicine")
    product_qty = fields.Integer(string="Quantity")
    appointment_id = fields.Many2one("hospital.appointment", string="Appointment ID")
