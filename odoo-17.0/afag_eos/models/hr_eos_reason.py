# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HREosReason(models.Model):
    _name = 'hr.eos.reason'
    _description = 'End Of service reasons'

    name = fields.Char(translate=True)
    type = fields.Selection([('resignation', 'Resignation'),
                                ('end_of_contract', 'End of Contract'),
                                ('no_compensation', 'No Compensation'),
                                ])
