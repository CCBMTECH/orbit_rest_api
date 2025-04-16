from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import hashlib
import hmac
import time
import logging
import urllib.parse

_logger = logging.getLogger(__name__)

class SendSms(models.Model):
    _name = 'orange.send.sms'
    _description = 'Send SMS'

    recipient = fields.Char('Recipient', required=True)
    message = fields.Text('Message', required=True ,utf8=True)
    status = fields.Selection(
        [
            ('pending', 'En attente'),
            ('sent', 'Envoyé'),
            ('failed', 'Echec'),
        ],
        string='Statut',
        default='pending',
    )

    def send_sms(self):
         
        config = self.env['orange.sms.config'].get_default_config()

        if not config:
            raise UserError(_("Please configure the SMS configuration."))

        login = config.login
        token = config.token
        api_key = config.api_key
        signature = config.signature

        if not login or not token or not api_key or not signature:
            raise UserError(_("Please configure the SMS configuration."))

        subject = "CCBM-SHOP"
        timestamp = int(time.time())
        
        # content = urllib.parse.quote(self.message, safe='')
        content = urllib.parse.quote_plus(self.message.encode('utf-8'), safe='')

        msg_to_encrypt = f"{token}{subject}{signature}{self.recipient}{content}{timestamp}"

        key = hmac.new(api_key.encode('utf-8'), msg_to_encrypt.encode('utf-8'), hashlib.sha1).hexdigest()
      
        try:
           
            parameters = {
                'token': token,
                'subject': subject,
                'signature': signature,
                'recipient': self.recipient,
                'content': self.message,
                'timestamp': timestamp,
                'key': key
            }
            

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            uri = f"https://api.orangesmspro.sn:8443/api"
            response = requests.post(uri, data=parameters , headers=headers, auth=(login, token))
            _logger.info(f"REPONSE API SMS: {response}")    
            # response.raise_for_status() 
            _logger.info(f"REPONSE API SMS: {response.text}")
            
            response_lines = response.text.strip().split('\n')
            response_dict = {}

            for line in response_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    response_dict[key.strip()] = value.strip()

            if  response_dict.get('STATUS_CODE') == 200:
                self.status = 'sent'
                self.message = "SMS sent successfully!"
            elif response_dict.get('STATUS_CODE') == 401:
                self.status = 'failed'
                self.message = "Error sending SMS: Unauthorized"
            else:
                self.status = 'failed'
                self.message = f"Error sending SMS: {response.text}"
                _logger.error(f"SMS sending failed. Status: {response_dict.get('STATUS_CODE')}, Message: {response_dict.get('STATUS_TEXT')}")

            self.env['orange.sms.history'].create({
                'recipient': self.recipient,
                'message': self.message,
                'status': self.status,
            })
        except Exception as e:
           

            self.status = 'failed'
            error_message = _("Error sending SMS: {}").format(str(e))
            self.env['orange.sms.history'].sudo().create({
                'recipient': self.recipient,
                'message': self.message,
                'status': 'failed',
                'send_date': fields.Datetime.now(),
            })
            _logger.error(error_message)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error"),
                    'message': error_message,
                    'type': 'danger',
                }
            }
        return {'type': 'ir.actions.act_window_close'}
