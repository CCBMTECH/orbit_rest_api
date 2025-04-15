#-*- encoding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.fields import Command
from odoo.exceptions import UserError


# TYPE_INVOICE = [
#     ('delivered', "Regular invoice"),
#     ('percentage', "Down payment (percentage)"),
#     ('fixed', "Down payment (fixed amount)"),
# ]

# TYPE_INVOICE_PREORDER = [
#     ('delivered', "Regular invoice")
# ]

READONLY_FIELDS = ['advance_payment_method',]
# class non utiliser
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    
    is_advance_invoice = fields.Boolean( string="Is Advance Invoice", compute="_compute_is_advance_invoice", store=False)
    
    def _compute_is_advance_invoice(self):
        for record in self:
            # Vérifie si le contexte contient 'is_advance_invoice'
            record.is_advance_invoice = self.env.context.get('is_advance_invoice', False)
        
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        
        if self._context.get('is_advance_invoice'):
            for field_name in READONLY_FIELDS:
                if field_name in res:
                    res[field_name]['readonly'] = True
                    
        return res
    


    # @api.constrains('product_id')
    # def _check_down_payment_product_is_valid(self):
    #     for wizard in self:
    #         if wizard.count > 1 or not wizard.product_id:
    #             continue

    #         # Condition supplémentaire : vérifier que la politique de facturation est dans ['order', 'delivery']
    #         if wizard.product_id.invoice_policy not in ['order', 'delivery']:
    #             raise UserError(_(
    #                 "The product used to invoice a down payment should have an invoice policy"
    #                 " set to either 'Ordered quantities' or 'Delivered quantities'."
    #                 " Please update your deposit product to be able to create a deposit invoice."))

    #         # Vérification du type de produit pour être un 'service'
    #         if wizard.product_id.type != 'service':
    #             raise UserError(_(
    #                 "The product used to invoice a down payment should be of type 'Service'."
    #                 " Please use another product or update this product."))

    # def _create_invoices(self, sale_orders, dates=None, amounts=None):
    #     self.ensure_one()

        
    #     if self.advance_payment_method == 'delivered':
    #         sale_orders.write({'state': 'sale'})
    #         res = sale_orders._create_invoices(final=self.deduct_down_payments)
    #         sale_orders.write({'state': 'to_delivered'})
    #         return res
    #     else:
    #         self.sale_order_ids.ensure_one()
    #         self = self.with_company(self.company_id)
    #         order = self.sale_order_ids

    #         invoices = []
    #         if dates and amounts:
    #             for i in range(3):  # Boucle pour créer 3 factures
    #                 # Créer le produit de dépôt si nécessaire
    #                 if not self.product_id:
    #                     self.product_id = self.env['product.product'].create(
    #                         self._prepare_down_payment_product_values()
    #                     )
    #                     self.env['ir.config_parameter'].sudo().set_param(
    #                         'sale.default_deposit_product_id', self.product_id.id)

    #                 # Créer la section de paiement anticipé si nécessaire
    #                 if not any(line.display_type and line.is_downpayment for line in order.order_line):
    #                     self.env['sale.order.line'].create(
    #                         self._prepare_down_payment_section_values(order)
    #                     )

    #                 down_payment_so_line = self.env['sale.order.line'].create(
    #                     self._prepare_so_line_values(order)
    #                 )

    #                 invoice = self.env['account.move'].sudo().create(
    #                     self._prepare_invoice_values(order, down_payment_so_line, dates[i], amounts[i])
    #                 ).with_user(self.env.uid)  # Unsudo the invoice after creation

    #                 invoice.message_post_with_view(
    #                     'mail.message_origin_link',
    #                     values={'self': invoice, 'origin': order},
    #                     subtype_id=self.env.ref('mail.mt_note').id)

    #                 invoice.action_post()

    #             invoices.append(invoice)

    #         return invoices

    # def _prepare_invoice_values(self, order, so_line, date, amount):
    #     self.ensure_one()
    #     return {
    #         **order._prepare_invoice(),
    #         'invoice_date': fields.Date.today(),
    #         'sale_id': order.id,
    #         'invoice_date_due': date,
    #         'invoice_line_ids': [
    #             Command.create(
    #                 so_line._prepare_invoice_line(
    #                     name=self._get_down_payment_description(order),
    #                     quantity=1.0,
    #                     price_unit=amount
    #                 )
    #             )
    #         ],
    #     }


    # def create_invoices(self):
    #     action = super(SaleAdvancePaymentInv, self).create_invoices()
    #     action['context']['default_sale_ref'] = self.sale_ref
    #
    #     return action


    # def _prepare_invoice_values(self, order, name, amount, so_line):
    #     res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
    #     res["sale_ref"] = order.name
    #
    #     return res

