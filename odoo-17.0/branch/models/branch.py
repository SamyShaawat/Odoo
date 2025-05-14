# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        args = domain or []
        if self._context.get('allowed_company_ids'):
            selected_company_ids = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
            if selected_company_ids:
                branches_ids = self.env['res.branch'].search([('company_id','in',selected_company_ids.ids)])
                domain += [('id', 'in', branches_ids.ids)]
            return super(ResBranch, self)._name_search(name=name, domain=domain, operator=operator, limit=limit,
                                                       order=order)
