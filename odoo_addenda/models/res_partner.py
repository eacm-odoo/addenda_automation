from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    addenda_addenda = fields.Many2one(
        comodel_name="addenda.addenda", string="Addenda Customed created by User")
    is_customed_addenda = fields.Boolean(string="Is Customed Addenda")
