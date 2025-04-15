# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TypeSale(models.TransientModel):
    _name = 'crm.type.sale'
    _description = 'Create new or use existing Customer on new Quotation'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        
        # Vérification du contexte
        if self._context.get('active_model') != 'crm.lead':
            raise UserError(_('This action can only be triggered from a lead.'))
        
        lead_id = self._context.get('active_id')
        if not lead_id:
            return result
            
        lead = self.env['crm.lead'].browse(lead_id)
        if not lead.exists():
            return result

        # Assignation des valeurs par défaut
        result['lead_id'] = lead.id
        
        # Recherche du partenaire de manière sécurisée
        partner = lead.partner_id or lead._find_matching_partner()
        if partner:
            result['partner_id'] = partner.id
            
        return result

    type_sale = fields.Selection(
        selection=[
            ('order', "Commande"),
            ('preorder', "Précommande"),
            ('creditorder', "Commande crédit"),
        ],
        string="Type de vente",
        required=True,
        default='order'  # Valeur par défaut recommandée
    )

    lead_id = fields.Many2one(
        'crm.lead', 
        "Lead associé",
        required=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        'Client',
        domain=[('customer_rank', '>', 0)],  # Filtre pour les clients
        required=True  # Obliger la sélection d'un client
    )

    def action_apply(self):
        self.ensure_one()
        
        # Gestion des erreurs
        if not self.partner_id:
            raise UserError(_("You must select a customer to continue."))
        
        # Assignation sécurisée du partenaire
        try:
            self.lead_id._handle_partner_assignment(
                force_partner_id=self.partner_id.id,
                create_missing=True  # Permet de créer un partenaire si nécessaire
            )
        except Exception as e:
            raise UserError(_("Partner assignment error: %s") % str(e))
        
        # Création de l'action avec contexte étendu
        action = self.lead_id.action_new_quotation()
        if action:
            action.update({
                'context': {
                    **action.get('context', {}),
                    'default_type_sale': self.type_sale,
                    'default_partner_id': self.partner_id.id,
                    'default_team_id': self.lead_id.team_id.id,
                }
            })
        
        return action
    
    
# class TypeSale(models.TransientModel):
#     _name = 'crm.type.sale'
#     _description = 'Create new or use existing Customer on new Quotation'


#     @api.model
#     def default_get(self, fields):
#         result = super(TypeSale, self).default_get(fields)

#         active_model = self._context.get('active_model')
#         if active_model != 'crm.lead':
#             raise UserError(_('You can only apply this action from a lead.'))

#         lead = False
#         if result.get('lead_id'):
#             lead = self.env['crm.lead'].browse(result['lead_id'])
#         elif 'lead_id' in fields and self._context.get('active_id'):
#             lead = self.env['crm.lead'].browse(self._context['active_id'])
#         if lead:
#             result['lead_id'] = lead.id
#             partner_id = result.get('partner_id') or lead._find_matching_partner().id
#             if 'partner_id' in fields and not result.get('partner_id'):
#                 result['partner_id'] = partner_id

#         return result

#     type_sale = fields.Selection(
#         selection = [
#             ('order', "Commande"),
#             ('preorder', "Precommande"),
#             # ('creditorder', "Commande credit"),
#         ],
#         string="Type", required=True)

#     lead_id = fields.Many2one('crm.lead', "Associated Lead", required=True)
#     partner_id = fields.Many2one('res.partner', 'Customer')

#     def action_apply(self):

#         self.ensure_one()
#         self.lead_id._handle_partner_assignment(force_partner_id=self.partner_id.id, create_missing=False)
#         action = self.lead_id.action_new_quotation()
#         if action:
#             action['context']['default_type_sale'] = self.type_sale
#         return action
