# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import date, datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


STATE = [
    ('draft', "Quotation"),
    ('sent', "Sent"),
    ('validation', "Validation"),
    ('sale', "Commande/Precommande"),
    ('to_delivered', "à livré"),
    ('delivered', "Livré"),
    ('done', "Locked"),
    ('cancel', "Cancelled"),
]

ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Sent"),
    ('validation', "Validation"),
    ('sale', "Commande"),
    ('to_delivered', "à livré"),
    ('delivered', "Livré"),
    ('done', "Locked"),
    ('cancel', "Cancelled"),
]

PREORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Sent"),
    ('validation', "Validation"),
    ('sale', "Pre-commande"),
    ('to_delivered', "à livré"),
    ('delivered', "Livré"),
    ('done', "Locked"),
    ('cancel', "Cancelled"),
]

CREDITORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Sent"),
    ('validation', "Validation"),
    ('sale', "Commande-credit"),
    ('to_delivered', "à livré"),
    ('delivered', "Livré"),
    ('done', "Locked"),
    ('cancel', "Cancelled"),
]

TYPE_SALE = [
    ('order', "Commande"),
    ('preorder', "Precommande"),
    ('creditorder', "Commande credit"),
]

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    

    def _get_steps(self):
        ctx = dict(self.env.context)
        selection = []
        if 'default_type_sale' in ctx:
            if ctx.get('default_type_sale') == 'order':
                selection = ORDER_STATE
            if ctx.get('default_type_sale') == 'preorder':
                selection = PREORDER_STATE
            if ctx.get('default_type_sale') == 'creditorder':
                selection = CREDITORDER_STATE
        else:
            selection = STATE

        return selection

    active = fields.Boolean("Active", default=True)
    
    # type de vente (type de business)
    type_sale = fields.Selection(
        selection=TYPE_SALE,
        string="Type Sale", required=True, readonly=True, copy=False, index=True,
        default = lambda self: self.env.context.get('default_type_sale', 'order'), 
        store=True
    )

    state = fields.Selection(
        selection=_get_steps,
        string="Status", readonly=True,
        copy=False, index=True,
        tracking=3, default='draft')
    
    # ----------------------------------------------------- Gestion des commandes échues ------------------------------------------------
    state_due = fields.Selection(
        selection=[
            ("not_due", "Non échu"),
            ("due", "échu"),
        ],
        default='not_due',
        string="État d'échéance", 
        store=True,
        compute="_compute_is_due", 
        help="Indique si la commande a des échéances à venir ou dépassées"
    )
    days_util_due = fields.Integer(
        string="Jours avant/après échéance", 
        compute="_compute_is_due", 
        store=True,
        help="Négatif pour les échéances à venir (-5 à 0), positif pour les retard"
    )
    overdue_amount = fields.Float(
        string="Montant échu", 
        compute="_compute_is_due", 
        store=True, 
        help="Montant total des échéances dépassées"
    )

    usr_confirmed = fields.Many2one('res.users', string="Confirmé par", readonly=True)
    
    partial_delivery_done = fields.Boolean(
        string="Livraison partielle effectuée",
        compute='_compute_partial_delivery',
        store=True
    )
    
    #----------------------------------------------------- Paiements -----------------------------------------------------
    # account_payment_ids = fields.One2many('account.payment', 'sale_id', string="Pay sale advanced", readonly=True)
    payment_count = fields.Float(compute_sudo=True, compute="_compute_advance_payment")
    amount_residual = fields.Float(
        "Residual Amount",
        readonly=True,
        compute_sudo=True,
        compute='_compute_advance_payment',
        digits=(16, 2),
        store=True
    )
    amount_payed = fields.Float('Payed Amount', compute_sudo=True, compute='_compute_advance_payment', digits=(16, 2), store=False)
    payment_line_ids = fields.Many2many(
        "account.move.line",
        string="Payment move lines",
        compute_sudo=True,
        compute="_compute_advance_payment",
        store=True,
    )
    advance_payment_status = fields.Selection(
        selection=[
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        store=True,
        readonly=True,
        copy=False,
        tracking=True,
        compute_sudo=True,
        compute="_compute_advance_payment",
    )
    
    # End Paiements ------------------------------------------------------------------------------------------------------
    
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'type_sale' not in vals and 'default_type_sale' in self.env.context:
                vals['type_sale'] = self.env.context['default_type_sale']

        return super(SaleOrder, self).create(vals_list)

    def action_to_delivered(self):
        for order in self:
            if order.type_sale == 'order':
                if order.amount_residual <= 0:
                    return order.write({ 'state': 'to_delivered' })  
                else:
                    raise ValidationError(_("Veuillez effectuer les paiements"))
            if order.type_sale == 'preorder':
                if order.amount_residual <= 0 and order.advance_payment_status == 'paid':
                    return order.write({ 'state': 'to_delivered' })
                else:
                    raise ValidationError(_("Veuillez effectuer les paiements"))
            if order.type_sale == 'creditorder':
                if order.validation_admin_state == 'validated' and order.first_payment_state:
                    return order.write({ 'state': 'to_delivered' })
                else:
                    raise ValidationError(_("Veuillez effectuer le paiement du premier acompte"))
            
    def action_delivered(self):
        for order in self:
            undelivered_lines = order.order_line.filtered(lambda line: line.qty_delivered < line.product_uom_qty)
            if undelivered_lines:
                undelivered_produts = ", ".join(undelivered_lines.mapped('product_id.name'))
                raise ValidationError(_("Veuillez effectuer la livraison des produits non livrés : {0}".format(undelivered_produts)))
            else:
               return order.write({'state': 'delivered'})
           
    # Gestion de facturation apres livraison
    def action_invoice_create(self):
        for order in self:
            if not order.partial_delivery_done:
                raise UserError(_("Impossible de facturer avant livraison complète/partielle des produits !"))
        return super().action_invoice_create()
    
    @api.depends('order_line.qty_delivered')
    def _compute_partial_delivery(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            order.partial_delivery_done = any(
                float_compare(line.qty_delivered, 0.0, precision_digits=precision) > 0
                for line in order.order_line
                if line.product_id.type in ['consu', 'product']
            )

    @api.model
    def cron_due_orders(self):
        # Récupérer toutes les commandes
        orders = self.search([])
        orders._compute_is_due()
        
    @api.depends('first_payment_date', 'first_payment_state', 'first_payment_amount',
                 'second_payment_date', 'second_payment_state', 'second_payment_amount',
                 'third_payment_date', 'third_payment_state', 'third_payment_amount',
                 'fourth_payment_date', 'fourth_payment_state', 'fourth_payment_amount',
                 'type_sale', 'validity_date', 'amount_residual', 'advance_payment_status')
    def _compute_is_due(self):
        current_date = fields.Date.context_today(self)
        for order in self:
            # Par défaut, on réinitialise les valeurs
            order.state_due = 'not_due'
            order.days_util_due = 0
            order.overdue_amount = 0.0

            # 1. Cas des commandes de type preorder et creditorder
            if order.type_sale in ['preorder', 'creditorder']:
                relevant_diffs = []
                overdue_total = 0.0
                payment_data = [
                    (order.first_payment_date, order.first_payment_state, order.first_payment_amount),
                    (order.second_payment_date, order.second_payment_state, order.second_payment_amount),
                    (order.third_payment_date, order.third_payment_state, order.third_payment_amount),
                    (order.fourth_payment_date, order.fourth_payment_state, order.fourth_payment_amount)
                ]
                for pay_date, pay_state, pay_amount in payment_data:
                    # On considère uniquement les échéances ayant une date et dont l'état n'est pas renseigné (non payé)
                    if pay_date and not pay_state:
                        days_diff = (current_date - pay_date).days
                        relevant_diffs.append(days_diff)
                        # Si l'échéance est dépassée (days_diff >= 0), on cumule le montant correspondant
                        if days_diff >= 0:
                            overdue_total += pay_amount

                if relevant_diffs:
                    # S'il y a au moins une échéance dépassée, on considère la commande comme due
                    overdue_diffs = [d for d in relevant_diffs if d > 0]
                    if overdue_diffs:
                        order.state_due = 'due'
                        # On prend le retard maximal pour information
                        order.days_util_due = max(overdue_diffs)
                        order.overdue_amount = overdue_total
                    else:
                        # Dans le cas où les échéances ne sont pas encore dépassées
                        order.state_due = 'not_due'
                        order.days_util_due = max(relevant_diffs)
                        order.overdue_amount = 0.0

            # 2. Cas des commandes de type order
            elif order.type_sale == 'order' and order.validity_date:
                # Si la date de validité est dépassée
                if order.validity_date < current_date:
                    # Et s'il reste un solde dû ou que le statut de paiement n'est pas "paid"
                    if order.amount_residual > 0 or order.advance_payment_status != 'paid':
                        order.state_due = 'due'
                        # Le nombre de jours en retard est calculé depuis la date de validité
                        order.days_util_due = (current_date - order.validity_date).days
                        # Ici, on considère le montant restant dû comme montant en retard
                        order.overdue_amount = order.amount_residual
                    else:
                        # Si le solde est réglé, on ne considère pas la commande comme due
                        order.state_due = 'not_due'
                        order.days_util_due = 0
                        order.overdue_amount = 0.0

            # 3. Pour les autres cas, on laisse les valeurs par défaut : non due
            else:
                order.state_due = 'not_due'
                order.days_util_due = 0
                order.overdue_amount = 0.0    
        

    @api.depends(
        'invoice_ids', 
        'invoice_ids.amount_total', 
        'invoice_ids.amount_residual', 
        'amount_total', 'currency_id', 
        'company_id'
    )
    def _compute_advance_payment(self):
        """
        
          
          Calcule les paiements anticipés d'un bon de commande en prenant en compte :
          - Les paiements réalisés sur les factures liées(normale ou accompte) au bo de commande.
          - Les paiements effectués (dont la reference contient le nom du bon de commande).
          
          
        """
        for order in self:
            payment_state = "not_paid"
            
            # 1. Récupérer les factures non annulées liées au bon de commande
            invoices = order.invoice_ids.filtered(lambda inv: inv.state != 'cancel')
            
            # 2. Calculer le montant payé sur les factures :
            #    Pour chaque facture, le paiement réalisé est égal au total facturé moins le résiduel restant.
            invoice_paid_amount = sum(inv.amount_total - inv.amount_residual for inv in invoices)
            
            # 3. Rechercher les paiements dont la référence contient le nom du bon de commande
            payments_by_reference = order.env['account.payment'].search([
                ('ref', 'ilike', order.name),
                ('state', '=', 'posted')
            ])
            payments_by_reference_amount = sum(payment.amount for payment in payments_by_reference)
            
            # 4. Totaliser les montants payés
            amount_payed = invoice_paid_amount + payments_by_reference_amount
            
            # 5. Calculer le résidu restant à payer sur le bon de commande
            amount_residual = order.amount_total - amount_payed
            
            # 6. Déterminer l'état de paiement en tenant compte de la précision de la devise
            if invoices:
                precision = order.currency_id.rounding
                residual_cmp = float_compare(amount_residual, 0.0, precision_rounding=precision)
                total_cmp = float_compare(amount_payed, order.amount_total, precision_rounding=precision)

                if residual_cmp <= 0 and total_cmp >= 0:
                    payment_state = "paid"
                elif amount_payed > 0:
                    payment_state = "partial"
                else:
                    payment_state = "not_paid"
            
            # 7. Pour le comptage des paiements, on combine :
            #    - Les paiements liés aux factures (filtrés sur ceux en état 'posted')
            #    - Les paiements retrouvés par référence
            valid_payments = len(order._get_valid_payments())
            
            # 8. Mise à jour du bon de commande avec les valeurs calculées
            order.update({
                'amount_payed': amount_payed,
                'amount_residual': amount_residual,
                'advance_payment_status': payment_state,
                'payment_count': valid_payments
            })
            