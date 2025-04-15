# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools, SUPERUSER_ID


class Opportunity2Quotation(models.TransientModel):
    _inherit = 'crm.quotation.partner'

    type_sale = fields.Selection(
        selection=[
            ('order', "Commande"),
            ('preorder', "Precommande"),
            ('creditorder', "Commande credit"),
        ],
        string="Type", required=True)

    def action_apply(self):

        action = super().action_apply()
        action['context']['default_type_sale'] = self.type_sale
        return action


