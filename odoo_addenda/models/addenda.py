from odoo import models, fields, api


class AddendaNode(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name')
    nodes_ids = fields.One2many(
        comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
