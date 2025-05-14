from email.policy import default

from chardet import detect_all
from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import ValidationError, UserError, AccessError, ValidationError, RedirectWarning
import base64
from io import BytesIO
from datetime import datetime, time, timedelta
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class InheritSaleOrderTemplateLine(models.Model):
    _inherit = 'sale.order.template.line'

    months = fields.Many2many('months.model')
    created = fields.Boolean('Created', readonly=True)

    def _prepare_order_line_values(self):
        """ Give the values to create the corresponding order line.

        :return: `sale.order.line` create values
        :rtype: dict
        """
        self.ensure_one()
        return {
            'display_type': self.display_type,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom_id.id,
            'sequence': self.sequence,
            'months': self.months.ids,
        }
