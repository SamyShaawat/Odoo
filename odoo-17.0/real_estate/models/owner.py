# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Owner(models.Model):
    _name = "owner"
    _description = "Owner Model"

    name = fields.Char(string="", required=True, default="owner")
    phone = fields.Char(string="", default="01091539396")
    address = fields.Char(string="", default="Alexandria, Egypt")
    property_ids = fields.One2many("property", "owner_id", string="Properties")
    _sql_constraints = [
        ('unique_name', 'unique("name")', 'This name is existing, please choose another one.'),
    ]
