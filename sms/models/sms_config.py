from odoo import models, fields, api
class SmsConfig(models.Model):
    _name = 'sms.config'
    _description = 'SMS Configuration'

    login = fields.Char('Login')
    token = fields.Char('Token')
    api_key = fields.Char('API Key')
    signature = fields.Char('Signature')

    @api.model
    def get_default_config(self):
        config = self.search([], limit=1)
        return config if config else False