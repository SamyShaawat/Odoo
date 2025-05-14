# -*- coding: utf-8 -*-
import itertools
import logging
import re
import json

from lxml import etree
from odoo import api, fields, models, tools, _



class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if not self.env.user.has_group('armchem_fields_access_rights.group_armchem_field_access_rights'):
                for node in doc.xpath("//field[@name='list_price']"):
                    node.set('readonly', '1')
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//field[@name='uom_id']"):
                    node.set('readonly', '1')
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//field[@name='seller_ids']"):
                    node.set('readonly', '1')
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc,encoding='unicode')
        return res
    