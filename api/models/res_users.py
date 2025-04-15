from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    def send_welcome_email(self):
        mail_template = self.env['mail.template'].sudo().search([('id', '=', 4)], limit=1)
        if not mail_template:
            raise ValueError("Mail template not found")

        for user in self:
            email_values = mail_template.generate_email([user.id], fields=['email_from', 'email_to', 'subject', 'body_html'])
            mail_mail = self.env['mail.mail'].sudo().create(email_values[user.id])
            mail_mail.send()

    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to ensure each user has a partner_id
        """
        for vals in vals_list:
            # Si partner_id n'est pas fourni, créer un partenaire
            if not vals.get('partner_id'):
                # Préparer les données du partenaire
                partner_vals = {
                    'name': vals.get('name', vals.get('login', 'New User')),
                    'email': vals.get('email', vals.get('login')),
                    'company_id': vals.get('company_id', self.env.company.id),
                }
                # Créer le partenaire
                partner = self.env['res.partner'].sudo().create(partner_vals)
                vals['partner_id'] = partner.id
        
        return super(ResUsers, self).create(vals_list)
