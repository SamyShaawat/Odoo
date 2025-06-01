# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Property(models.Model):
    _name = "property"
    _description = "Property Model"
    # _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="", required=True, default="property", size=12)
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
    owner_id = fields.Many2one("owner", string="", required=True)
    tag_ids = fields.Many2many("tag", string="")

    _sql_constraints = [
        ('unique_name', 'unique("name")', 'This name is existing, please choose another one.'),
    ]

    @api.constrains('bedrooms')
    def _check_bedrooms_greater_zero(self):
        for rec in self:
            if rec.bedrooms == 0:
                raise ValidationError("The number of bedrooms cannot be Zero.")

    @api.model_create_multi
    def create(self, vals):
        res = super(Property, self).create(vals)
        # or res = super().create(self,vals)
        print("inside create method of property model")
        return res

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        res = super(Property, self)._search(domain, offset=0, limit=None, order=None, access_rights_uid=None)
        print("inside search method of property model")
        return res

    def write(self, vals):
        res = super(Property, self).write(vals)
        # or res = super().write(self, vals)
        print("inside write method of property model")
        return res

    def unlink(self):
        res = super(Property, self).unlink()
        # or res = super().unlink(self)
        print("inside unlink method of property model")
        return res
