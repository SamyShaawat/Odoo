# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, _
_logger = logging.getLogger(__name__)
class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def _eval_context(self):
        res = super(IrRule, self)._eval_context()
        branch_ids = self.env.context.get('allowed_branch_ids', [])
        branches = self.env['res.branch']
        if branch_ids:
            branches = self.env['res.branch'].sudo().browse(branch_ids)
        if branches:
            res['branch_ids'] = branches.ids
        else:
            res['branch_ids'] = self.env.user.sudo().branch_id.sudo().ids if self.env.user.sudo().branch_id else []
        return res

    def _compute_domain_keys(self):
        """ Return the list of context keys to use for caching ``_compute_domain``. """
        return super(IrRule, self)._compute_domain_keys() + ['allowed_branch_ids']