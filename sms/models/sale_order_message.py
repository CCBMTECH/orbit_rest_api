from odoo import models, fields

class SaleOrderMessage(models.Model):
    _name = 'sale.order.message'
    _description = 'Message de Commande'

    name = fields.Char(string='Titre')
    message = fields.Text(string='Message')
    sale_order_id = fields.Many2one('sale.order', string='Commande')
