# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _, exceptions
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import float_compare

import logging

_logger = logging.getLogger(__name__)


class Preorder(models.Model):
    _description = 'Preorder Order'
    _inherit = 'sale.order'

    is_fixed_invoice = fields.Boolean( string="Is Advance Invoice", compute="_compute_payment_data", store=True)
    
    # Les dates 
    date_approved_creditorder = fields.Datetime("Date confirmation commande credit", store=True)
    first_payment_date = fields.Date("Date du Premier Paiement", compute='_compute_reminder_dates', store=True, help="Définie à la date de confirmation de commande")
    second_payment_date = fields.Date("Date du Deuxième Paiement", compute='_compute_reminder_dates', store=True, help="30 jours avant livraison pour précommandes")
    third_payment_date = fields.Date("Date du Troisième Paiement", compute='_compute_reminder_dates', store=True) 
    fourth_payment_date = fields.Date("Date du Quatrième Paiement", compute='_compute_reminder_dates', store=True, help="90 jours après approbation pour crédit")

    # Montants à payer
    first_payment_amount = fields.Monetary("1er amount", compute="_compute_payment_data", currency_field='currency_id', store=True)
    second_payment_amount = fields.Monetary("2nd amount", compute="_compute_payment_data", currency_field='currency_id', store=True)
    third_payment_amount = fields.Monetary("3rd amount", compute="_compute_payment_data", currency_field='currency_id', store=True)
    fourth_payment_amount = fields.Monetary("4rd amount", compute="_compute_payment_data", currency_field='currency_id', store=True)

    # Status de paiements
    first_payment_state = fields.Boolean(string="Statut 1er paiement", compute='_compute_payment_data', store=True)
    second_payment_state = fields.Boolean(string="Statut 2nd paiement", compute='_compute_payment_data', store=True)
    third_payment_state = fields.Boolean(string="Statut 3rd paiement", compute='_compute_payment_data', store=True)
    fourth_payment_state = fields.Boolean(string="Statut 4rd paiement", compute='_compute_payment_data', store=True)

    # Commande à crédit
    validation_rh_state = fields.Selection([
        ('pending', 'Validation en cours'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ], string='Validation RH client', required=True, default='pending')
    validation_rh_date = fields.Date(string='Date de Validation RH', readonly=True)
    validation_rh_partner_id = fields.Many2one('res.partner', string="Utilisateur RH", readonly=True)

    validation_admin_state = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ], string='Validation responsable vente', required=True, default='pending', )
    validation_admin_date = fields.Date(string='Date de Validation Admin', readonly=True)
    validation_admin_user_id = fields.Many2one('res.users', string="Utilisateur Admin", readonly=True)
    validation_admin_comment = fields.Text(string='Commentaire Admin', readonly=True)


    # ----------------------------------------------- Methodes ------------------------------------------------------
    def validate_rh(self):

        for order in self:
            # Vérification de l'appartenance de l'utilisateur au groupe requis
            if self.env.user.has_group("orbit.credit_group_user"):
                entreprise = order.partner_id.parent_id
                _logger.info(f"ID Entreprise de l'employe === : {order.partner_id.parent_id.id}")
                if entreprise and entreprise.id != 2:
                    # Filtrer pour obtenir le responsable principal de la validation
                    user_main = order.partner_id.parent_id.child_ids.filtered(lambda p: p.role == 'main_user')
                    if user_main:
                        user_main = user_main[0]
                        order.write({
                            'validation_rh_state': 'validated',
                            'validation_rh_date': fields.Datetime.now(),
                            'validation_rh_partner_id': user_main.id
                        })
                    else:
                        raise exceptions.ValidationError(_("Aucun utilisateur avec le rôle Principal n'est défini dans l'entreprise associée du client."))
                else:
                    # Si l'entreprise n'est pas définie, utiliser l'utilisateur actuel
                    order.write({
                        'validation_rh_state': 'validated',
                        'validation_rh_date': fields.Datetime.now(),
                        'validation_rh_partner_id': self.env.user.id
                    })
            else:
                raise exceptions.ValidationError(_(
                    "Vous n'avez pas les droits requis pour valider cette commande. "
                    "Veuillez contacter un utilisateur ayant les permissions nécessaires dans le groupe 'Utilisateur Crédit'."
                    ))

    def reject_rh(self):
        for order in self:
            order.write({
                'validation_rh_state': 'rejected',
                'validation_rh_date': fields.Datetime.now(),
                'validation_rh_partner_id': self.partner_id.id
            })

    def approved_responsable(self):
        for order in self:
            order.write({
                'validation_admin_state': 'validated',
                'validation_admin_date': fields.Datetime.now(),
                'validation_admin_user_id': self.env.user.id,
            })

    def rejected_responsable(self):
        for order in self:
            order.write({
                'validation_admin_state': 'rejected',
                'validation_admin_date': fields.Datetime.now(),
                'validation_admin_user_id': self.env.user.id,
            })
    
    def send_resp_client(self):
        for order in self:
            order.write({
                'state': 'validation', 
                })

    # @api.depends('order_line.invoice_lines')
    # def _get_invoices(self):
    #     # The invoice_ids are obtained thanks to the invoice lines of the SO
    #     # lines, and we also search for possible refunds created directly from
    #     # existing invoices. This is necessary since such a refund is not
    #     # directly linked to the SO.
    #     for order in self:
    #         invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
    #         order.invoices = invoices

    def action_view_payments(self):
        """Action pour visualiser les paiements liés"""
              
        if not self._get_valid_payments():
            raise UserError(_("Aucun paiement trouvé pour cette commande"))

        payments = self._get_valid_payments()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_payments')
        action.update({
            'domain': [('id', 'in', payments.ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_ref': self.name,
                'default_date': fields.Date.context_today(self),
                'default_amount': self._get_next_payment_amount(),
                'search_default_group_by_payment_type': True
            },
            'views': [(False, 'list'), (False, 'form')]
        })
        
        return action

    def _get_next_payment_amount(self):
        """Calcule dynamiquement le montant du prochain paiement attendu"""
        payments = self._get_valid_payments()
        paid = sum(payments.mapped('amount'))
        thresholds = [
            self.first_payment_amount,
            self.first_payment_amount + self.second_payment_amount,
            self.amount_total
        ]
        
        for threshold in thresholds:
            if paid < threshold:
                return threshold - paid
        return 0.0
    
    # ------------------------------------------ computes methods ----------------------------------------------------
    
    def _get_valid_payments(self):
        """ Retourne les paiements valides liés à la commande par les factures ou via la référence du bon de commande """
        self.ensure_one()
        invoice_names = self.invoice_ids.mapped('name')
        domain = [
            ('is_internal_transfer', '=', False), 
            ('state', '=', 'posted'), 
            '|', 
            ('ref', 'in', invoice_names), 
            ('ref', 'ilike', self.mapped('name')), 
            # ('ref', 'in', self.mapped('name'))
        ]
        payments = self.env['account.payment'].search(domain, order="date desc")
        
        return payments
        
    @api.depends(
        'order_line.price_total',
        'payment_term_id',
        'currency_id',
        'company_id',
        'type_sale',
        'amount_residual',
        'date_approved_creditorder',
        'transaction_ids.state',
        'invoice_ids.amount_residual'
    )
    def _compute_payment_data(self):
        """Calcule les échéances de paiement et leur statut en respectant la précision monétaire"""
        
        for order in self:
            # Initialisation du dictionnaire de paiement
            payment_data = {}
            for prefix in ['first', 'second', 'third', 'fourth']:
                payment_data[f'{prefix}_payment_amount'] = 0.0
                payment_data[f'{prefix}_payment_state'] = False
                
            payment_data['is_fixed_invoice'] = False
                
            # Gestion sécurisée de la devise
            try:
                currency = order.currency_id or order.company_id.currency_id
                currency.ensure_one()
            except ValueError:
                order.update(payment_data)
                continue
            
            # Récupération et conversion des paiements
            paid_amount = 0.0
            payments = order._get_valid_payments()
            for payment in payments:
                try:
                    paid_amount += payment.currency_id._convert(
                        payment.amount,
                        currency,
                        order.company_id,
                        payment.date or fields.Date.today()
                    )
                except (ValueError, UserError) as e:
                    _logger.error(f"Erreur conversion devise paiement {payment.id}: {str(e)}")
            
            paid_amount = currency.round(paid_amount)

            # Calcul des montants et statuts
            order_lines = order.order_line.filtered(lambda l: not l.is_downpayment)
            total_amount = currency.round(sum(order_lines.mapped('price_total'))) if order_lines else 0.0

            if total_amount > 0 and order.type_sale in ['preorder', 'creditorder']:
                payment_config = order._get_payment_structure()
                cumulative_amount = 0.0

                for percentage, field_prefix in payment_config.get('structure', []):
                    amount = currency.round(total_amount * percentage)
                    payment_data[f'{field_prefix}_payment_amount'] = amount
                    cumulative_amount += amount
                    threshold = cumulative_amount
                    payment_data[f'{field_prefix}_payment_state'] = currency.compare_amounts(paid_amount, threshold) >= 0

                # Validation finale d'arrondi
                if not currency.is_zero(cumulative_amount - total_amount):
                    _logger.warning(f"Erreur d'arrondi commande {order.name}: {cumulative_amount} vs {total_amount}")
                
                if payment_config.get('use_residual'):
                    final_stage = payment_config.get('final_stage')
                    payment_data[f"{final_stage}_payment_state"] = currency.is_zero(order.amount_residual)
                
                if order.amount_residual > 0:
                    payment_data['is_fixed_invoice'] = True

            order.update(payment_data)
        
    def _get_payment_structure(self):
        """ Retourne la structure de paiement selon le type de commande """
        
        if self.type_sale == 'preorder':
            return {
                'structure': [
                    (0.3, 'first'),
                    (0.3, 'second'),
                    (0.4, 'third')
                ],
                'final_stage': 'third',
                'use_residual': True
            }
        elif self.type_sale == 'creditorder':
            return {
                'structure': [
                    (0.5, 'first'),
                    (0.2, 'second'),
                    (0.15, 'third'),
                    (0.15, 'fourth')
                ],
                'final_stage': 'fourth',
                'use_residual': True
            }
        return {'structure': []}

    @api.depends('date_order', 'commitment_date', 'date_approved_creditorder', 'type_sale')
    def _compute_reminder_dates(self):
        for order in self:
            # Réinitialiser toutes les dates par défaut
            order.update({
                'first_payment_date': False,
                'second_payment_date': False,
                'third_payment_date': False,
                'fourth_payment_date': False,
            })
            
            if order.type_sale == 'preorder':
                if order.date_order and order.commitment_date:
                     # Conversion datetime à date avec timezone utilisateur
                    dt = fields.Datetime.context_timestamp(order, order.date_order)
                    order.first_payment_date = dt.date()
                    # Calcul des dates relatives
                    order.second_payment_date = order.commitment_date - timedelta(days=30)
                    order.third_payment_date = order.commitment_date  # Date de Livraison
            
            elif order.type_sale == 'creditorder':
                if order.date_approved_creditorder:
                    # Conversion datetime approuvé en date locale
                    approved_dt = fields.Datetime.context_timestamp(
                        order, 
                        order.date_approved_creditorder
                    )
                    base_date = approved_dt.date()
                    # Calcul avec intervalles mensuels relatifs
                    order.first_payment_date = base_date
                    order.second_payment_date = base_date + relativedelta(months=1)
                    order.third_payment_date = base_date + relativedelta(months=2)
                    order.fourth_payment_date = base_date + relativedelta(months=3) # Date de Livraison

    
    def action_cancel(self):
        res = super(Preorder, self).action_cancel()
        
        for order in self:
            if order.type_sale == 'creditorder':
                order.write({
                    'validation_rh_state': 'cancelled',
                    'validation_admin_state': 'cancelled',
                })
                
        return res
    
    def _set_delivery_state(self):
        """Transition contrôlée vers l'état de livraison"""
        if self.amount_residual <= 0:
            self.write({
                'state': 'to_delivered',
                'usr_confirmed': self.env.user.id
            })
    
    def action_confirm(self):
        
        res = super().action_confirm()
        
        for order in self:
            # Traitement des commandes standards
            if order.type_sale == 'order':
                pass
                
            # Gestion des précommandes avec création de factures échelonnées
            elif order.type_sale == 'preorder':
                if not all([self.first_payment_date, self.second_payment_date, self.third_payment_date]):
                    raise ValidationError(_("Dates de paiement manquantes pour la précommande"))
                
                # payment_data = [
                #     (self.first_payment_date, self.first_payment_amount),
                #     (self.second_payment_date, self.second_payment_amount),
                #     (self.third_payment_date, self.third_payment_amount)
                # ]
                
                # dates = [self.first_payment_date, self.second_payment_date, self.third_payment_date]
                # amounts = [self.first_payment_amount, self.second_payment_amount, self.third_payment_amount]
                
                try:
                    # self._create_advance_invoices(dates, amounts)
                    # self._create_structured_invoices(payment_data)
                    pass
                except Exception as e:
                    _logger.error("Erreur création facture précommande: %s", str(e))
                    raise
                
            # Validation stricte des commandes crédit
            elif order.type_sale == 'creditorder':
                validation_checks = [
                    (self.validation_rh_state != 'validated', 
                    _("Validation RH du client requise.")),
                    (self.validation_admin_state != 'validated',
                    _("Validation Responsale de vente manquante")),
                    (not self.first_payment_state,
                    _("Premier acompte non payé"))
                ]

                for condition, error_msg in validation_checks:
                    if condition:
                        raise UserError(error_msg)

                self.date_approved_creditorder = fields.Datetime.now()

            # Enregistre l'utilisateur connecté    
            order.usr_confirmed = self.env.user
            return res    
            
    # -------------------------------------------------- Envoyer un email de rappel -------------------------------------
    @api.model
    def action_send_due_emails(self):
        """ 
        Envoie :
          - Pour les commandes de type 'preorder' et 'creditorder' :
              * Un email informatif 2 jours avant une date d'échéance (sur l'une des échéances de paiement non réglées).
              * Un email de rappel 5 jours après, si la commande est échu (state_due = 'due' et délai de retard >= 5 jours).
          - Pour les commandes de type 'order' :
              * Un email de rappel 3 jours après la date d'échéance (basé sur validity_date) si la commande est échu.
        """
        current_date = fields.Date.context_today(self)
        sale_order_obj = self.env['sale.order']

        # --- Pour les commandes de type 'preorder' et 'creditorder' ---
        orders_pre = sale_order_obj.search([
            ('type_sale', 'in', ['preorder', 'creditorder']),
            # On peut affiner la recherche éventuellement sur les commandes non payées
        ])

        for order in orders_pre:
            # 1. Email informatif 2 jours AVANT l'échéance pour une échéance non encore réglée.
            # On vérifie pour chacune des échéances de paiement renseignées.
            send_informative = False
            payment_dates = [
                (order.first_payment_date, order.first_payment_state),
                (order.second_payment_date, order.second_payment_state),
                (order.third_payment_date, order.third_payment_state),
                (order.fourth_payment_date, order.fourth_payment_state)
            ]
            for pay_date, pay_state in payment_dates:
                if pay_date and not pay_state:
                    # Si la date d'échéance est dans 2 jours exactement
                    if (pay_date - current_date).days < 0 and (pay_date - current_date).days >= -2:
                        send_informative = True
                        break

            if send_informative:
                # On utilise un modèle d'email préconfiguré pour l'information
                template = self.env.ref('orbit.preorder_creditorder_informative_template', raise_if_not_found=False)
                if template:
                    template.send_mail(order.id, force_send=True)

            # 2. Email de rappel 5 jours APRÈS l'échéance si la commande est échu
            # On se base sur le champ calculé "days_util_due" qui indique le nombre de jours de retard
            if order.state_due == 'due' and order.days_util_due >= 5:
                template = self.env.ref('orbit.preorder_creditorder_reminder_template', raise_if_not_found=False)
                if template:
                    template.send_mail(order.id, force_send=True)

        # --- Pour les commandes de type 'order' ---
        orders_order = sale_order_obj.search([
            ('type_sale', '=', 'order'),
            ('validity_date', '!=', False),  # On s'assure que la date d'échéance est renseignée
            ('state_due', '=', 'due')
        ])
        for order in orders_order:
            # Si la commande est échue, on envoie un email 3 jours APRÈS la date d'échéance (validity_date)
            if (current_date - order.validity_date).days >= 3:
                template = self.env.ref('orbit.order_overdue_reminder_template', raise_if_not_found=False)
                if template:
                    template.send_mail(order.id, force_send=True)
                    
        


