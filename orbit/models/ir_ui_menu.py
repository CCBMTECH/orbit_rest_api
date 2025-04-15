# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, exceptions


class RestrictMenu(models.Model):
    _inherit = 'ir.ui.menu'

    # Champ Many2many pour lier les utilisateurs restreints
    restrict_user_ids = fields.Many2many(
        'res.users',
        string='Utilisateurs restreints',
        help='Liste des utilisateurs qui ne peuvent pas accéder à ce menu.'
    )
    
    # @api.model
    # def _filter_visible_menus(self, menus):
    #     # Filtrer les menus visibles en fonction des utilisateurs restreints
    #     user_id = self.env.user.id
    #     filtered_menus = menus.filtered(lambda menu: user_id not in menu.restrict_user_ids.ids)
    #     return super(RestrictMenu, self)._filter_visible_menus(filtered_menus)
    