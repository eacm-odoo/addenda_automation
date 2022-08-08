from odoo import models, fields


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    addenda_id = fields.Many2one(
        comodel_name='addenda.addenda', string='Addenda')
