# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """ Add information about iap enrich to perform """
        user = request.env.user
        session_info = super(Http, self).session_info()

        if self.env.user.has_group('base.group_user'):
            session_info.update({
                "user_branches": {
                    'current_branch': user.branch_id.id, 
                    'allowed_branches': {
                        branch.id: {
                            'id': branch.id,
                            'name': branch.name,
                            'company': branch.company_id.id,
                        } for branch in user.branch_ids
                    },
                },
                "currencies": self.get_currencies(),
                "show_effect": True,
                "display_switch_company_menu": user.has_group('base.group_multi_company') and len(user.company_ids) > 1,
                "display_switch_branch_menu": user.has_group('branch.group_multi_branch') and len(user.branch_ids) > 1,
                "allowed_branches": user.branch_id.ids
            })
        return session_info
