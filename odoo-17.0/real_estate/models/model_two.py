from odoo import models, fields, api, _


class ModelTwo(models.TransientModel):
    _name = "model.two"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Model Two"
    # _rec_name = "model_two"
