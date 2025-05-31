# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Property(models.Model):
    _name = "property"
    _description = "Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="", required=True, default="property", size=10)
    description = fields.Text(string="")
    postcode = fields.Char(string="", required=True)
    date_availability = fields.Date(string="", required=True, default=fields.Date.context_today)
    expected_price = fields.Float(string="", digits=(0, 1))
    selling_price = fields.Float(string="", digits=(0, 1))
    bedrooms = fields.Integer(string="", required=True)
    living_area = fields.Integer(string="")
    facades = fields.Integer(string="")
    garage = fields.Boolean(string="")
    garden = fields.Boolean(string="")
    garden_area = fields.Integer(string="")
    garden_orientation = fields.Selection([
        ("north", "North"),
        ("south", "South"),
        ("east", "East"),
        ("west", "West"),
    ], string="", default="north")

    @api.constrains('bedrooms')
    def _check_bedrooms_greater_zero(self):
        for rec in self:
            if rec.bedrooms == 0:
                raise ValidationError("The number of bedrooms cannot be Zero.")
