from odoo import models, fields, api, _


class AddendaAttribute(models.Model):
    _name = 'addenda.attribute'
    _description = 'Addenda attributes'

    addenda_tag_id = fields.Many2one(
        comodel_name='addenda.tag', string='Addenda tag')
    addenda_node_id = fields.Many2one(
        comodel_name='addenda.node', string='Addenda node')
    attribute = fields.Char(string='Attribute', help=_(
        'Name of the attribute of the new tag'), required=True)
    value = fields.Char(string='Attribute Value', help=_(
        'Value of the attribute of the new tag'))
    field = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'many2one', 'monetary', 'integer', 'boolean', 'date', 'datetime'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    field_type = fields.Char(compute='_compute_field_type', default='')
    inner_field_domain = fields.Char(
        string='Inner field domain', help=_('Domain to filter the inner field'))

    @api.depends('field')
    def _compute_field_type(self):
        for record in self:
            record.field_type = record.field.ttype

    @api.onchange('field')
    def _compute_inner_fields_domain(self):
        for record in self:
            if record.field:
                record.inner_field_domain = record.field.relation