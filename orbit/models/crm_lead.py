# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Lead(models.Model):
    _inherit = "crm.lead"


    location = fields.Char('Localisation', store=True)

    # def action_sale_quotations_new(self):
    #     if not self.partner_id:
    #         return self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
    #     else:
    #         return self.env["ir.actions.actions"]._for_xml_id("orbit.crm_type_sale_action")
    
    def action_sale_quotations_new(self):
        """
        Redirige vers l'action appropriée pour créer un nouveau devis.
        - Si aucun partenaire n'est défini, ouvre la vue de sélection d'un partenaire.
        - Si un partenaire est défini, redirige vers la création d'un devis.
        """
        # Vérifie si un partenaire est associé
        if not self.partner_id:
            # Retourne l'action pour sélectionner un partenaire
            return self.env.ref("sale_crm.crm_quotation_partner_action").read()[0]
        else:
            # Retourne l'action pour créer un devis
            return self.env.ref("orbit.crm_type_sale_action").read()[0]

