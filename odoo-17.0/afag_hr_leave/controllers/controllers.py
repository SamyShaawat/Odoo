# -*- coding: utf-8 -*-
# from odoo import http


# class AfagHrLeave(http.Controller):
#     @http.route('/afag_hr_leave/afag_hr_leave', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/afag_hr_leave/afag_hr_leave/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('afag_hr_leave.listing', {
#             'root': '/afag_hr_leave/afag_hr_leave',
#             'objects': http.request.env['afag_hr_leave.afag_hr_leave'].search([]),
#         })

#     @http.route('/afag_hr_leave/afag_hr_leave/objects/<model("afag_hr_leave.afag_hr_leave"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('afag_hr_leave.object', {
#             'object': obj
#         })

