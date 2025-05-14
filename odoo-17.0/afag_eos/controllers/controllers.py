# -*- coding: utf-8 -*-
# from odoo import http


# class AfagEos(http.Controller):
#     @http.route('/afag_eos/afag_eos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/afag_eos/afag_eos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('afag_eos.listing', {
#             'root': '/afag_eos/afag_eos',
#             'objects': http.request.env['afag_eos.afag_eos'].search([]),
#         })

#     @http.route('/afag_eos/afag_eos/objects/<model("afag_eos.afag_eos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('afag_eos.object', {
#             'object': obj
#         })

