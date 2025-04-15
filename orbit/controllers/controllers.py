# -*- coding: utf-8 -*-
# from odoo import http


# class Orbit(http.Controller):
#     @http.route('/orbit/orbit', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/orbit/orbit/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('orbit.listing', {
#             'root': '/orbit/orbit',
#             'objects': http.request.env['orbit.orbit'].search([]),
#         })

#     @http.route('/orbit/orbit/objects/<model("orbit.orbit"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('orbit.object', {
#             'object': obj
#         })
