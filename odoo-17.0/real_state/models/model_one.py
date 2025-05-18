# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RealState(models.Model):
    _name = "model.one"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Model One"
    # _rec_name = "model_one"
