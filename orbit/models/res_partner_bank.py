# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = "res.partner.bank"

    iban = fields.Char('IBAN')
    bic = fields.Char('BIC')

