from odoo import models, fields, api, _


class ModelThree(models.AbstractModel):
    _name = "model.three"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Model Three"
    # _rec_name = "model_three"
