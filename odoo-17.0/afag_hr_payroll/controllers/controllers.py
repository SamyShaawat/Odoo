# -*- coding: utf-8 -*-
# from odoo import http


# class AfagHrPayroll(http.Controller):
#     @http.route('/afag_hr_payroll/afag_hr_payroll', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/afag_hr_payroll/afag_hr_payroll/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('afag_hr_payroll.listing', {
#             'root': '/afag_hr_payroll/afag_hr_payroll',
#             'objects': http.request.env['afag_hr_payroll.afag_hr_payroll'].search([]),
#         })

#     @http.route('/afag_hr_payroll/afag_hr_payroll/objects/<model("afag_hr_payroll.afag_hr_payroll"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('afag_hr_payroll.object', {
#             'object': obj
#         })

