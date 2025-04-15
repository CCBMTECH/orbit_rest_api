# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from datetime import datetime


class ResPartner(models.Model):
    _inherit = "res.partner"


    entreprise_code = fields.Char(string="ID Entreprise", default="Code")
    register_com = fields.Char('Registre Commercial')
    ninea = fields.Char(string='NINEA')

    role = fields.Selection([
            ('main_user', 'Utilisateur Principal'),
            ('secondary_user', 'Utilisateur Secondaire')
        ], string='Role', default='secondary_user')
    adhesion = fields.Selection([
            ('pending', 'En cours de validation'),
            ('accepted', 'Accepté'),
            ('rejected', 'Rejeté')
        ], string='Adhésion', default='pending')
    
    # Nouveau champ pour le responsable du suivi
    payment_responsible_id = fields.Many2one('res.users', string='Follow-up Responsible',
                                             help="Optionally you can assign a user to this field, which will make him responsible for the action.",
                                             copy=False, ondelete='set null', )

    # Nouveau champ pour la promesse de paiement du client
    payment_note = fields.Text('Customer Payment Promise', help="Payment Note", copy=False)

    # Nouveau champ pour la prochaine action
    payment_next_action = fields.Text('Next Action', copy=False,
                                      help="This is the next action to be taken. It will automatically be set when the partner gets a follow-up level that requires a manual action.",
                                      )

    # Nouveau champ pour la date de la prochaine action
    payment_next_action_date = fields.Date('Next Action Date', copy=False,
                                           help="This is when the manual follow-up is needed. "
                                                "The date will be set to the current date when the partner "
                                                "gets a follow-up level that requires a manual action. "
                                                "Can be practical to set manually e.g. to see if he keeps "
                                                "his promises.")

    # # Nouveau champ pour les écritures comptables non réconciliées
    # unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id',
    #                                        domain=[('reconciled', '=', False), ('move_id.state', '!=', 'draft')])

    


    # @api.model_create_multi
    # def create(self, vals_list):
    #     """ Méthode pour générer un code unique basé sur le nom, la date de création et le rang de l'entreprise """

    #     for vals in vals_list:
    #         if vals.get('is_company', None):
    #             code_date_creation = datetime.now().strftime('%d%m%Y')
    #             code_number = self.search_count([('is_company', '=', True)]) + 1
    #             code_name = str(vals.get('name')[0:4]).upper()
    #             vals['entreprise_code'] = f"{code_name}{code_date_creation}{code_number}"

    #             return super(ResPartner, self).create(vals)
    #         else:
    #             return super(ResPartner, self).create(vals)
    
    

    @api.model_create_multi
    def create(self, vals_list):
        """ Génère un code unique pour les entreprises avec nom/date/incrément """
        # Récupère le nombre d'entreprises existant AVANT création
        base_company_count = self.search_count([('is_company', '=', True)])
        current_increment = 1
        code_date = datetime.now().strftime('%d%m%Y')  # Date commune pour tous
        
        # Traitement de toutes les entrées en une passe
        for vals in vals_list:
            if vals.get('is_company'):
                # Formatage des éléments du code
                name_part = (vals.get('name', '')[:4] or 'UNKN').upper()  # Fallback 'UNKN'
                sequential_number = base_company_count + current_increment
                
                # Construction du code final
                vals['entreprise_code'] = f"{name_part}{code_date}{sequential_number}"
                current_increment += 1
        
        # Création groupée standard
        return super(ResPartner, self).create(vals_list)
        

