# alkhatim tech.

from odoo import api, models,fields

class Branch(models.Model):
    _inherit = 'res.branch'

    sequence_applied = fields.Boolean('Apply Branch Sequence Prefix?')
    pre_sequence_branch = fields.Char('Branch Prefix Sequence')


