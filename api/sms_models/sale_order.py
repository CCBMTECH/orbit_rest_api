# File: models/sale_order.py
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_send_sms(self):
        self.ensure_one()
        
        products = '\n'.join(line.product_id.name for line in self.order_line if line.product_id and line.product_id.name and line.product_id.name != 'Acompte')
        type_order = ""
        if self.type_sale == 'order':
            type_order = 'Commande'
        elif self.type_sale == 'preorder':
            type_order = 'Précommande'
        elif self.type_sale == 'creditorder':
            type_order = 'Commande à crédit'

        message = (
            f"Bonjour {self.partner_id.name},\n"
            f"Détails de la {type_order} #{self.name}:\n\n"
            f"Produits:\n{products}\n"
            f"Montant total: {self.amount_total} {self.currency_id.symbol}"
        )
        recipient = self.partner_id.phone
        return {
            'type': 'ir.actions.act_window',
            'name': 'Envoyer SMS',
            'res_model': 'orange.send.sms',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_recipient': recipient,
                'default_message': message,
            }
        }