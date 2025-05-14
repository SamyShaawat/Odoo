# alkhatim tech.

from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    # sequence_prefix = fields.Char(compute=False)

    # def action_post(self):
    #     res = super(AccountMove, self).action_post()
    #     if self.branch_id.sequence_applied:
    #         # prefix = self.journal_id.sequence_id.prefix
    #         self.name = self.branch_id.pre_sequence_branch + "/" + self.name
    #     return res
