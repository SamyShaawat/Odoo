# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ModelFour(models.Model):
    _name = "model.four"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Model Four"
    _log_access = True
    # _rec_name = "model_four"
