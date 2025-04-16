from odoo import models, fields, api

class TestOrangeSMS(models.Model):
    _name = 'test.orange.sms'
    _description = 'Test Orange SMS'

    recipient = fields.Char('Recipient', required=True)
    message = fields.Text('Message', required=True)

    def send_sms(self):
        self.env['send.sms'].create({
            'recipient': self.recipient,
            'message': self.message,
        }).send_sms()

    def view_sms_history(self):
        return {
            'name': 'SMS History',
            'type': 'ir.actions.act_window',
            'res_model': 'sms.history',
            'view_mode': 'tree,form',
            'domain': [('recipient', '=', self.recipient)],
        }
