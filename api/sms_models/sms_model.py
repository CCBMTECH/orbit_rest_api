from odoo import models, fields, api

class SmsModel(models.Model):
    _name = 'orange.sms.model'
    _description = 'SMS Model'

    code = fields.Char('Code', required=True)
    message = fields.Text('Message', required=True)
    parametre = fields.Char('Paramètre', required=True)

    @api.onchange('parametre')
    def onchange_parametre(self):
        self.message = self.message.replace("]","").replace("[","")
