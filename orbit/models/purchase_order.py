#-*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    attachment_ids = fields.Many2many(
        'ir.attachment',
        relation='purchase_order_attachment_rel',  # Nom de relation plus explicite
        column1='purchase_order_id',
        column2='attachment_id',
        string="Attachments",
        help="Attached documents related to this purchase order"
    )
    
    date_approve = fields.Datetime(
        string='Confirmation Date', readonly=True, copy=False, tracking=True
    )
    
    confirmed_by_user_id = fields.Many2one(
        'res.users',
        string="Confirmed By",
        readonly=True,
        copy=False,
        tracking=True
    )
    
    is_locked = fields.Boolean(string="Verrouillé", store=False, help="Indique si le bon d'achat est verrouillé en lecture seule.")
    
    @api.depends('state')
    def _compute_is_locked(self):
        for order in self:
            if order.state in ['purchase', 'done']:
                order.is_locked = True
            else:
                order.is_locked = False

    
    # def write(self, vals):
    #     # Autoriser les opérations système et pièces jointes
    #     system_context = self.env.context.get('tracking_disable') or self._context.get('bypass_purchase_lock')
    #     if system_context or self.env.user.has_group('base.ccbmshop_purchase_group_manager'):
    #         return super().write(vals)
        
    #     # Autoriser spécifiquement l'annulation
    #     if vals.get('state') in ['draft', 'to approve', 'sent']:
    #         return super().write(vals)
        
    #     # Vérifier si la restriction doit être appliquée
    #     if not self.env.context.get('bypass_purchase_lock'):
    #         for order in self.filtered(lambda o: o.state in ['purchase', 'done']):
    #             # Whitelist étendue avec champs techniques nécessaires
    #             allowed_fields = self._get_whitelisted_fields()
    #             if not set(vals.keys()).issubset(allowed_fields):
    #                 _logger.info(f"Tentative de modification non autorisée par {self.env.user.name} sur {order.name}")
    #                 raise UserError(_("Modification non autorisée sur le bon de commande %s confirmé ! (État: %s).") % (order.name, order.state))
        
    #     return super().write(vals)


    def _get_whitelisted_fields(self):
        """Retourne la liste des champs modifiables après confirmation."""
        return {
            
            'notes',    # Notes internes
            'state',    # État de la commande
            'priority',  # Priorité de la commande
            'attachment_ids',  # Pièces jointes
            
            'message_main_attachment_id',  # Champ critique pour les pièces jointes
            'activity_ids',                # Gestion des activités
            'message_ids'                 # Historique de messages
            'write_uid',
            'write_date',
        }
    
    def button_confirm(self):
        """Confirme le bon de commande et enregistre l'utilisateur qui confirme."""
        # Validation personnalisée avant confirmation
        # self._check_confirm_validation()
        
        # self = self.with_context(bypass_purchase_lock=True)
        res = super().button_confirm()
        
        # Mise à jour en masse pour optimiser les performances
        self.write({
            'confirmed_by_user_id': self.env.user.id,
            'date_approve': fields.Datetime.now()  # Optionnel : date de confirmation
        })
        
        return res
    
    # Validation optionelle avant confirmation (à personnaliser)
    # def _check_confirm_validation(self):
    #     """Add custom validation rules before confirmation"""
        
    #     # Vérification du groupe utilisateur
    #     if not self.env.user.has_group('orbit.ccbmshop_purchase_group_manager'):
    #         raise UserError(_("Permission refusée - Contactez un manager pour confirmer."))


    # def button_confirm(self):
    #     """Overrides the confirm button method to record the user who confirmed."""
    #     res = super(PurchaseOrder, self).button_confirm()
    #     for order in self:
    #         # Enregistre l'utilisateur connecté
    #         order.usr_confirmed = self.env.user  
    #     return res
    
    # def button_confirm(self):
    #     """Override confirm button to track confirming user and add validation"""
    #     # Validation personnalisée avant confirmation
    #     self._check_confirm_validation()

    #     # Appel de la méthode originale avec contexte
    #     # result = super(PurchaseOrder, self.with_context(
    #     #     mail_notify_author=True
    #     # )).button_confirm()
        
    #      # Appel de la méthode originale
    #     result = super().button_confirm()
        
    #     # Mise à jour en masse pour optimiser les performances
    #     self.write({
    #         'confirmed_by_user_id': self.env.user.id,
    #         'date_approve': fields.Datetime.now()  # Optionnel : date de confirmation
    #     })
        
    #     # Post-confirmation processing
    #     # self._post_confirm_actions()
    #     return result

    # Validation optionelle avant confirmation (à personnaliser)
    # def _check_confirm_validation(self):
    #     """Add custom validation rules before confirmation"""
        
    #     for order in self:
    #         # Vérification du groupe utilisateur
    #         if not order.env.user.has_group('orbit.purchase_ccbmshop_group_user'):
    #             raise UserError(_("Accès refusé - Vous devez appartenir au groupe 'Validation Achats CCBMShop'"))
        
    #         # if not order.attachment_ids:
    #         #     raise UserError(_("Please attach required documents before confirming."))
    #         # if order.amount_total > 10000 and not self.env.user.has_group('purchase.group_purchase_manager'):
    #         #     raise UserError(_("Manager approval required for orders over $10,000."))

    # def _post_confirm_actions(self):
    #     """Execute post-confirmation actions"""
    #     # Envoi automatique d'email avec pièces jointes
    #     template = self.env.ref('purchase.email_template_edi_purchase')
    #     for order in self:
    #         template.with_context(attachments=order.attachment_ids).send_mail(order.id)
    
    # def _log_activity(self):
    #     """Journalisation des confirmations"""
    #     self.message_post(
    #         body=_("Commande confirmée par %s") % self.env.user.name,
    #         subject="Confirmation de commande"
    #     )
    