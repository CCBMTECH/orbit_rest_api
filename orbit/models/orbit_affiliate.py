# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class Affiliate(models.Model):

    # ---------------------------------------- Private Attributes ---------------------------------
    _name = "orbit.affiliate"
    _description = "Program Affiliate"
    _order = "name desc, id desc"
    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "The name for Partner must be unique"),
        ("name_partner", "UNIQUE(partner_id)", "The Company for Partner must be unique"),
    ]

    # --------------------------------------- Fields Declaration ----------------------------------
    # Basic
    name = fields.Char("Affiliate Partner", index=True)
    active = fields.Boolean("Active", default=True)
    #sequence = fields.Integer('Sequence')

    create_date = fields.Datetime("Date Creation", index=True, readonly=False, default=lambda self: fields.Datetime.now())
    date_closed = fields.Datetime('Date Archivage', copy=False)

    currency_id = fields.Many2one('res.currency', string='Monnaie')
    amount_credit_total = fields.Monetary(string="Crédit Total", currency_field='currency_id', store=True)
    amount_credit_progressing = fields.Monetary(string="Crédit en cours", currency_field='currency_id', store=True)

    # ------------------- Informations sur l'Entreprise ------------------- #
    partner_id = fields.Many2one('res.partner', string="Nom Entreprise",
                                 required=True, readonly=False, copy=False, index=True, domain=[('is_company', '=', True)])
    # Secteur d'activité de l'entreprise
    partner_activity = fields.Char(string="Secteur activité", store=True, compute='_compute_data')
    partner_mobile = fields.Char(related='partner_id.mobile', string='Mobile', store=True, compute='_compute_data')
    partner_phone = fields.Char(related='partner_id.phone', string='Telephone', store=True, compute='_compute_data')
    partner_email = fields.Char(related='partner_id.email', string='Email', store=True, compute='_compute_data')
    # partner_address = fields.Char("Adresse ", help="Adresse physique de l'entreprise")
    partner_register_com = fields.Char(related='partner_id.register_com', string='Registre Commercial', store=True, compute='_compute_data')
    partner_ninea = fields.Char(related='partner_id.ninea', string='NINEA', store=True, compute='_compute_data')
    # Nombre d'employés
    partner_taille = fields.Char("Taille Entreprise", help="Nombre d'employés ou chiffre d'affaires")
    # Address fields
    street = fields.Char('Street', compute='_compute_data', readonly=False, store=True)
    street2 = fields.Char('Street2', compute='_compute_data', readonly=False, store=True)
    zip = fields.Char('Zip', change_default=True, compute='_compute_data', readonly=False, store=True)
    city = fields.Char('City', compute='_compute_data', readonly=False, store=True)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_data', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', string='Country',
        compute='_compute_data', readonly=False, store=True)
    # charger fichier Partenaire
    file_affiliate = fields.Binary(string='Fichier Partenariat', store=True)

    # Infos du contact principal
    main_contact = fields.Many2one('res.partner', string="Contact principal", readonly=False, domain=[('is_company', '=', False), ('is_main_contact', '=', True)])
    mobile_main_contact = fields.Char(string="Mobile Principal")
    email_main_contact = fields.Char("E-mail")
    function_main_contact = fields.Char("Fonction")

    # Détails du programme
    interest = fields.Selection([('oui', "Oui"), ('non', "Non")], string='Intérêt pour le partenariat')
    comment = fields.Html("CommentaireBesoins et Objectifs",
                          help="Les besoins, les objectifs et les avantages recherchés spécifiques de l'entreprise partenaire concernant le partenariat.")
    duration = fields.Float("Durée des crédits")
    # méthode de paiement
    moyen_payment = fields.Char("Méthode de paiement",
                                help="Conditions de paiement préférentielles souhaitées par l'entreprise partenaire exple: paiements mensuels, etc")
    #note_exigences = fields.Text("Autres exigences ou commentaires", help="Toute autre exigence ou commentaire spécifique de l'entreprise partenaire")

    # Coordonnées Bancaire
    partner_bank_id = fields.Many2one('res.partner.bank', string="Banque Entreprise")
    partner_bank_name = fields.Char("Nom Banque",)
    partner_acc_number = fields.Float("Compte Bancaire")
    iban = fields.Char("IBAN")
    bic = fields.Char("BIC")

    #name_admin = fields.Char("Name admin")
    user_id = fields.Many2one(comodel_name='res.users', string="User", readonly=False,
                              default=lambda self: self.env.user, index=True)


    # @api.model
    # def create(self, vals):
    #     self.send_notification_to_group('orbit.group_orbit_admin')
    #     return super().create(vals)

    # @api.depends('partner_id.email')
    # def _compute_email_from(self):
    #     for lead in self:
    #         if lead.partner_id.email and lead._get_partner_email_update():
    #             lead.email_from = lead.partner_id.email

    # def _inverse_email_from(self):
    #     for lead in self:
    #         if lead._get_partner_email_update():
    #             lead.partner_id.email = lead.email_from
    # @api.onchange('partner_id')
    @api.onchange('main_contact')
    def _onchange_contact_main(self):
        # main_contacts = self.partner_id.child_ids.filtered(lambda c: c.type == 'contact' and c.is_main_contact == True)
        # self.main_contact = main_contacts[0] if main_contacts else False
        if self.main_contact:
            self.function_main_contact = self.main_contact.function
            self.email_main_contact = self.main_contact.email
            self.mobile_main_contact = self.main_contact.mobile
            #self.telephone_cp = self.contact_principal.phone

    @api.depends('partner_bank_id')
    def _compute_bank_data(self):
        for affiliate in self:
            if affiliate.partner_bank_id:
                affiliate.partner_bank_name = affiliate.partner_bank_id.name
                affiliate.partner_acc_number = affiliate.partner_bank_id.acc_number

    @api.depends('partner_id')
    def _compute_data(self):
        for affiliate in self:
            if affiliate.partner_id:
                affiliate.partner_phone = affiliate.partner_id.phone
                affiliate.partner_mobile = affiliate.partner_id.mobile
                affiliate.partner_email = affiliate.partner_id.email
                affiliate.partner_register_com = affiliate.partner_id.register_com
                affiliate.partner_ninea = affiliate.partner_id.ninea
                affiliate.partner_taille = len(affiliate.partner_id.child_ids)

                # Adresse du partenaire
                affiliate.street = affiliate.partner_id.street
                affiliate.street2 = affiliate.partner_id.street2
                affiliate.zip = affiliate.partner_id.zip  # code postal
                affiliate.city = affiliate.partner_id.city  # ville
                affiliate.state_id = affiliate.partner_id.state_id # Pays
                affiliate.country_id = affiliate.partner_id.country_id # continent

                # Secteur d'activité du partenaire
                activities = list()
                if affiliate.partner_id.category_id:
                    for elt in affiliate.partner_id.category_id:
                        name = elt.name
                        activities.append(name)

                activities_name = ", ".join(activities)
                affiliate.partner_activity = activities_name

        return

    # def send_notification_to_group(self, group_name):
    #     # Récupération des utilisateurs appartenant au groupe spécifié
    #     group = self.env.ref(group_name)
    #     group_id = group.id
    #     users = self.env['res.users'].search([('groups_id', 'in', [group_id])])
    #
    #     # Envoyer une notification à l'Admin par e-mail
    #     for user in users:
    #         self.name_admin = user.name
    #         template_id = self.env.ref('orbit.mail_notification_admin').id or self.notification_template.id
    #         template = self.env['mail.template'].browse(template_id)
    #         if template:
    #             template.send_mail(self.id, force_send=True, email_values={
    #                 'email_to': user.email,
    #             })
    #         else:
    #             raise UserError(_("Template not found."))



