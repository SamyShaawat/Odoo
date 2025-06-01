# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Tag(models.Model):
    _name = "tag"
    _description = "Tag Model"

    name = fields.Char(string="", required=True, default="tag")
