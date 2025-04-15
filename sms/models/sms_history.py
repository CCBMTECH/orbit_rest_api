from odoo import models, fields

class SmsHistory(models.Model):
    _name = 'sms.history'
    _description = 'SMS History'

    recipient = fields.Char('Recipient')
    message = fields.Text('Message')
    status = fields.Selection(
        [
            ('pending', 'En attente'),
            ('sent', 'Envoyé'),
            ('failed', 'Echec'),
        ],
        string='Statut',
        default='pending',
    )
    send_date = fields.Datetime('Date d\'envoi', default=fields.Datetime.now)
