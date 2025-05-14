# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command


class Partner(models.Model):
    _inherit = "res.partner"

    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.uid,
                              help='The internal user in charge of this contact.')
    credit_limit = fields.Float('Credit Limit')

    def _get_name(self):
        partner = self
        name = super(Partner, self)._get_name()
        if self._context.get('show_street'):
            name = "%s, %s" % (partner.street or '', partner.street2 or '')
        return name

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            args += args
        elif self.user_has_groups('sales_team.group_sale_salesman'):
            args += ['|', '|', ('id', 'in', self.env.user.company_ids.mapped('partner_id').ids),
                     ('id', '=', self.env.user.company_id.partner_id.id),
                     ('user_id', '=', self.env.user.id)]
        elif self.user_has_groups('base.group_portal'):
            args += args
        else:
            args += ['|', '|', ('id', 'in', self.env.user.company_ids.mapped('partner_id').ids),
                     ('id', '=', self.env.user.company_id.partner_id.id),
                     ('user_id', '=', self.env.user.id)]
        return super(Partner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            args += args
        # elif self.user_has_groups('sales_team.group_sale_salesman'):
        #     args += ['|','&',('parent_id','!=',False),('user_id','=',self.env.user.id),'&',('category_id.name','=','Customers'),'|', '|', ('id', 'in', self.env.user.company_ids.mapped('partner_id').ids),
        #              ('id', '=', self.env.user.company_id.partner_id.id),
        #              ('user_id', '=', self.env.user.id)]

        elif self.user_has_groups('base.group_portal'):
            args += args
        elif self.user_has_groups('sales_team.group_sale_salesman'):
            args += ['|', '|', ('id', 'in', self.env.user.company_ids.mapped('partner_id').ids),
                     ('id', '=', self.env.user.company_id.partner_id.id),
                     ('user_id', '=', self.env.user.id)]
        else:
            if len(args) == 1 and len(args[0]) == 3 and args[0][:2] == ('parent_id', 'in') \
                    and args[0][2] != [False]:
                self = self.with_context(active_test=False)
        return super(Partner, self)._search(args, offset=offset, limit=limit, order=order,
                                            count=count, access_rights_uid=access_rights_uid)

    def open_one2many_line(self):
        context = self.env.context
        view_id = self.env.ref('armchem_sale_partner_addresses.armchem_view_partner_address_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Address',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': self._name,
            'res_id': context.get('default_active_id'),
            'target': 'new',
        }

    def action_view_sale_order(self):
        action = self.env['ir.actions.act_window']._for_xml_id('sale.act_res_partner_2_sale_order')
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        action["context"] = {'create': True, 'edit': True, 'default_partner_id': self.id}
        return action
