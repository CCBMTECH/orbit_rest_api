# -*- coding: utf-8 -*-
from odoo import  fields, models, api, _, exceptions
import logging

_logger = logging.getLogger(__name__)

class Users(models.Model):
    _inherit = 'res.users'

    signature_perso = fields.Binary(string="Signature Perso", attachment=True)


    # @api.model_create_multi
    # def create(self, vals_list):

    #     self.clear_caches()
    #     usrs = super(Users, self).create(vals_list)

    #     # Recupérer les groupe : "Groupe portal", "Internal User" et "Groupe public"
    #     portal_group = self.env.ref('base.group_portal')  # Identifier le groupe "Portal"
    #     internal_group = self.env.ref('base.group_user')  # Groupe "Internal User"
    #     public_group = self.env.ref('base.group_public')  # Groupe "Public"
    #     # _logger.info(f" portal_group: {portal_group}, internal_group: {internal_group}, public_group: {public_group} .")
    #     for usr in usrs:
    #         # Retirer l'utilisateur des autres types d'utilisateurs
    #         usr.groups_id = [(3, internal_group.id), (3, portal_group.id), (4, public_group.id)]

    #     return usrs
    
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Users, self).fields_get(allfields, attributes)
        if not self.env.user.has_group('base.group_system'):  # Groupe de Managers
            if 'signature_perso' in res:
                res['signature_perso']['readonly'] = True
            if self.env.user == self:
                res['signature_perso']['readonly'] = False  # L'utilisateur peut modifier sa propre signature
        return res
    
    def write(self, vals_list):
        """
        Else the menu will be still hidden even after removing from the list
        """
        usrs = super(Users, self).write(vals_list)
        for rec in self:
            for menu in rec.hide_menu_ids:
                menu.write({
                    'restrict_user_ids': [(4, rec.id)]
                })
        self.clear_caches()
        return usrs
    
    def _get_is_admin(self):
        """
        The Hide specific menu tab will be hidden for the Admin user form.
        Else once the menu is hidden, it will be difficult to re-enable it.
        """
        for usr in self:
            usr.is_admin = False
            if usr.id == self.env.ref('base.user_admin').id:
                usr.is_admin = True

    hide_menu_ids = fields.Many2many('ir.ui.menu', string="Menus", store=True, 
                                     help="Select menu items that needs to be hidden to this user ")
    is_admin = fields.Boolean(string="Est Admin", compute=_get_is_admin)
    