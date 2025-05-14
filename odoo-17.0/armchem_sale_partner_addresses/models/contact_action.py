# -*- coding: utf-8 -*-
from odoo import models, _


class Partner(models.Model):
    _name = 'contact.action'

    def action_open_contacts(self):
        result = {
            "name": "Contacts",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "search_view_id": self.env.ref("base.view_res_partner_filter", False).id,
            "context": {'create': False, 'edit': True, 'default_is_company': True},
            'view_mode': 'kanban,tree,form,activity,google_map',
        }

        if self.user_has_groups('sales_team.group_sale_salesman') and not (
                self.user_has_groups('sales_team.group_sale_salesman_all_leads') or self.user_has_groups(
            'sales_team.group_sale_manager')):
            result["domain"] = [('category_id.name', '=', 'Customers')]

        return result
