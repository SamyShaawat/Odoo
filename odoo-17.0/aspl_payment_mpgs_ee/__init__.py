# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider
def post_init_hook(env):
    setup_provider(env, 'mpgs')


def uninstall_hook(env):
    reset_payment_provider(env, 'mpgs')