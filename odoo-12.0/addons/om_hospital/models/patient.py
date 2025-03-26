# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


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
    @api.onchange("new_name")
    def _onchange_new_name(self):
        if self.new_name:
            self.sale_order_count = self.env["sale.order"].search_count(
                [("partner_id", "=", self.new_name.id)]
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

    patient_name = fields.Char(string="Name", required=True)
    patient_age = fields.Integer("Age")
    notes = fields.Text(string="Registration Note")
    image = fields.Binary(string="Image", attachment=True)
    name = fields.Char(string="Test")
    name_seq = fields.Char(
        string="Patient ID",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("fe_male", "Female"),
        ],
        default="male",
        string="Gender",
    )
    age_group = fields.Selection(
        [
            ("major", "Major"),
            ("minor", "Minor"),
        ],
        string="Age Group",
        compute="set_age_group",
        store=True,
    )
    new_name = fields.Many2one(comodel_name="res.partner", string="New Name")
    sale_order_count = fields.Integer(
        string="No. of Sale Orders", compute="_onchange_new_name", store=True
    )
