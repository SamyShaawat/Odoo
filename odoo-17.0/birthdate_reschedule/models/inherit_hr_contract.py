import logging
import base64
from datetime import date

from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class InheritHrContract(models.Model):
    _inherit = "hr.contract"

    birthdate = fields.Date("Birth Date")

    def _execute_send_birthdate_email(self):
        if self.birthdate:
            days_before_birthday = self.birthdate - fields.Date.today()
            if days_before_birthday.days <= 3:
                html_body = """
                  <font size='2'>
                    Dear Customer <br/>
                    Happy Birthday 
                </font>
                """
                mail = {
                    'subject': "BirthDate Congrats",
                    'email_from': 'mh9557686@gmail.com',
                    'email_to': '{}'.format(self.employee_id.work_email),
                    'body_html': html_body,
                }
                mail_create = self.env['mail.mail'].create(mail)
                if mail_create:
                    mail_create.send()

    def _auto_send_partner_ledger(self):
        contract_to_send = self.search([])
        for contract in contract_to_send:
            try:
                contract._execute_send_birthdate_email()
            except UserError as e:
                _logger.exception(e)
