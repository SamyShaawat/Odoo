# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


# Inheriting the Sale Order Model and Adding New Field
class SaleOrderInherit(models.Model):
    _inherit = "sale.order"
    patient_name = fields.Char(string="Patient Name")


class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Patient Record"
    _rec_name = "patient_name"

    # task from fathy
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.sale_order_count = self.env["sale.order"].search_count(
                [("partner_id", "=", self.partner_id.id)]
            )
        else:
            self.sale_order_count = 0

    # Overriding the create method to assign sequence for the record
    @api.model
    def create(self, vals):
        if vals.get("name_seq", _("New")) == _("New"):
            vals["name_seq"] = self.env["ir.sequence"].next_by_code(
                "hospital.patient.sequence"
            ) or _("New")
        result = super(HospitalPatient, self).create(vals)
        return result

    # How to Write Compute Field and its Function in Odoo12
    @api.depends("patient_age")
    def set_age_group(self):
        for rec in self:
            if rec.patient_age:
                if rec.patient_age < 18:
                    rec.age_group = "minor"
                else:
                    rec.age_group = "major"

    # Add Constrains For a Field
    @api.constrains("patient_age")
    def check_age(self):
        for rec in self:
            if rec.patient_age <= 5:
                raise ValidationError(_("Age must be greater than 5."))

    # Action For Smart Button
    @api.multi
    def open_patient_appointments(self):
        return {
            "name": _("Appointments"),
            "domain": [("patient_id", "=", self.id)],
            "view_type": "form",
            "res_model": "hospital.appointment",
            "view_id": False,
            "view_mode": "tree,form",
            "type": "ir.actions.act_window",
        }

    def get_appointment_count(self):
        count = self.env["hospital.appointment"].search_count(
            [("patient_id", "=", self.id)]
        )
        self.appointment_count = count

    patient_name = fields.Char(string="Name", required=True, track_visibility="always")
    patient_age = fields.Integer(string="Age", track_visibility="always")
    notes = fields.Text(string="Registration Note", track_visibility="always")
    appointment_count = fields.Integer(
        string="Appointment", compute="get_appointment_count"
    )
    image = fields.Binary(string="Image", attachment=True, track_visibility="always")
    name = fields.Char(string="Contact Number")
    name_seq = fields.Char(
        string="Patient ID",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
        track_visibility="always",
    )
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("fe_male", "Female"),
        ],
        default="male",
        string="Gender",
        track_visibility="always",
    )
    age_group = fields.Selection(
        [
            ("major", "Major"),
            ("minor", "Minor"),
        ],
        string="Age Group",
        compute="set_age_group",
        store=True,
        track_visibility="always",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner ID", track_visibility="always"
    )
    sale_order_count = fields.Integer(
        string="No. of Sale Orders",
        compute="_onchange_partner_id",
        store=True,
        track_visibility="always",
    )
    # field to connect the patient with an existing Odoo User
    user_id = fields.Many2one(
        "res.users",
        string="Related User",
        track_visibility="always",
    )
