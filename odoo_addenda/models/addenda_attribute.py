from odoo import models, fields, api, _


class AddendaAttribute(models.Model):
    _name = 'addenda.attribute'
    _description = 'This module allows the user add many attributes to one tag in the addenda'

    addenda_tag_id = fields.Many2one(
        comodel_name='addenda.tag', string='Addenda tag')
    addenda_node_id = fields.Many2one(
        comodel_name='addenda.node', string='Addenda node')
    attribute = fields.Char(string='Attribute', help=(
        'Name of the attribute of the new tag'), required=True)
    value = fields.Char(string='Attribute Value', help=(
        'Value of the attribute of the new tag'))
    field = fields.Many2one(
        string='Field', help=('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'many2one', 'monetary', 'integer', 'boolean', 'date', 'datetime'))])
    inner_field = fields.Many2one(
        string='Inner field', help=('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    field_type = fields.Char(compute='_compute_field_type', default='')
    inner_field_domain = fields.Char(
        string='Inner field domain', help=('Domain to filter the inner field'))

    @api.depends('field')
    def _compute_field_type(self):
        for attribute in self:
            if attribute.field:
                attribute.field_type = attribute.field.ttype
            else:
                attribute.field_type = False

    @api.onchange('field')
    def _generate_inner_fields_domain(self):
        for attribute in self:
            if attribute.field:
                attribute.inner_field_domain = attribute.field.relation
            else:
                attribute.inner_field_domain = False
