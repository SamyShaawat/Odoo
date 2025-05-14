# from odoo import api, models, SUPERUSER_ID
#
# class CreateJournal(models.Model):
#     _name = 'create.journal'
#
#     @api.model
#     def _create_journal(self):
#         journal_exists = self.env['account.journal'].search([('code', '=', 'COM')], limit=1)
#         if not journal_exists:
#             journal_vals = {
#                 'name': 'Commission',
#                 'code': 'COM',
#                 'type': 'miscellaneous',
#                 'company_id': self.env.user.company_id.id,
#                 'currency_id': self.env.user.company_id.currency_id.id,
#             }
#             self.env['account.journal'].create(journal_vals)
#
# @api.model
# def post_init_hook(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     env['create.journal']._create_journal()
