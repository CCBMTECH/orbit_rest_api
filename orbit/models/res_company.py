# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class Company(models.Model):
    _inherit = 'res.company'

    # main_user_id = fields.Many2one('res.partner', string='Responsable Principal')

    # # Changer le role du responsable d'entreprise à chaque modification du responsable principal
    # @api.depends("main_user_id")
    # def assign_role(self):
    #     self.main_user_id.role = 'main_user'
