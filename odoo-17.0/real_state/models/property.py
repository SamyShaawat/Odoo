from odoo import models, fields, api, _


class Property(models.Model):
    _name = "property"
    _description = "Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="")
    description = fields.Text(string="")
    postcode = fields.Char(string="")
    date_availability = fields.Date(string="")
    expected_price = fields.Float(string="")
    selling_price = fields.Float(string="")
    bedrooms = fields.Integer(string="")
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
    ], string="")
