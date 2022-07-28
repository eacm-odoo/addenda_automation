from odoo import models, fields, api, _


class AddendaCfdiAttributes(models.Model):
    _name = 'addenda.cfdi.attributes'
    _description = 'Attributes from the cfdi'

    name = fields.Char(string='Attribute', required=True)
    value = fields.Char(string='Value', required=True)
    node = fields.Char(string='Node', required=True)
    nodes_ids = fields.One2many(
        comodel_name='addenda.node', string='Nodes', inverse_name='cfdi_attributes')
    