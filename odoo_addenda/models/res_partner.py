from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_mx_edi_addenda_customed = fields.Many2one(
        comodel_name="ir.ui.view", string="Addenda Customed")
    is_customed_addenda = fields.Boolean(string="Is Customed Addenda")
