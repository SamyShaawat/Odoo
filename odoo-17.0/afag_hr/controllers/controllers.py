# -*- coding: utf-8 -*-
# from odoo import http


# class SaudiHr(http.Controller):
#     @http.route('/afag_hr/afag_hr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/afag_hr/afag_hr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('afag_hr.listing', {
#             'root': '/afag_hr/afag_hr',
#             'objects': http.request.env['afag_hr.afag_hr'].search([]),
#         })

#     @http.route('/afag_hr/afag_hr/objects/<model("afag_hr.afag_hr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('afag_hr.object', {
#             'object': obj
#         })

