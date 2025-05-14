# -*- encoding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID
from odoo import api


def post_init_hook(env):
    """
    website menu hide
    """
    env.cr.execute("""
                update ir_model_data set noupdate=False where
                model ='ir.rule' """)
