from lxml.objectify import fromstring
from lxml import etree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AddendaTag(models.Model):
    _name = 'addenda.tag'
    _description = 'Add tag to node in addenda'

    addenda_node_id = fields.Many2one(
        string='Addenda Node', comodel_name='addenda.node')
    addenda_addenda_id = fields.Many2one(
        string='Addenda Addenda', comodel_name='addenda.addenda')
    addenda_tag_childs_ids = fields.One2many(
        comodel_name='addenda.tag', string='Addenda Tag Childs', inverse_name='addenda_tag_id', help=_('New elements added inside this tag/element'))
    addenda_tag_id = fields.Many2one(
        string='Addenda tag', comodel_name='addenda.tag')
    tag_name = fields.Char(string='Tag Name', required=True,
                           help=_('Name of the new tag/element'))
    attribute = fields.Char(string='Attribute', help=_(
        'Name of the attribute of the new element'))
    value = fields.Char(string='Attribute Value', help=_(
        'Value of the attribute of the new element'))
    field = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'many2one', 'monetary', 'integer', 'boolean', 'date', 'datetime'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    preview = fields.Text(store=False, string='Preview',
                          readonly=True, compute='_compute_preview', help=_('A preview to hel the user to create the xml'))

    field_type = fields.Char(compute='_compute_field_type', default='')
    len_tag_childs = fields.Integer(compute='_compute_len_child_tags')

    @api.depends('addenda_tag_childs_ids')
    def _compute_len_child_tags(self):
        self.len_tag_childs = len(self.addenda_tag_childs_ids)

    @api.onchange('field')
    def _compute_inner_fields(self):
        domain = {'inner_field': []}
        for record in self:
            if record.field:
                record.addenda_tag_childs_ids = False
                if record.field.ttype == 'many2one':
                    domain = {'inner_field': [
                        ('model', '=', record.field.relation), ('ttype', '!=', 'many2one')]}
        return {'domain': domain}

    @api.onchange('addenda_tag_childs_ids')
    def _child_ids_attribute_onchange(self):
        for record in self:
            if (len(record.addenda_tag_childs_ids) > 0 and not record.attribute):
                record.field = False
                record.inner_field = False
                record.value = False

    @api.onchange('value')
    def _value_onchange(self):
        for record in self:
            if record.value:
                record.field = False
                record.inner_field = False

    @api.depends('field')
    def _compute_field_type(self):
        for record in self:
            record.field_type = record.field.ttype

    @api.depends('tag_name', 'attribute', 'value', 'field', 'addenda_tag_childs_ids', 'inner_field')
    def _compute_preview(self):
        for record in self:
            tag = record.tag_name or 'TagName'
            attr = ('t-att-' + record.attribute ) if record.attribute else ''
            value = ''
            body = ''
            record.preview = ''
            attrs={}
            if record.value and record.attribute:
                attrs[attr]=record.value
            elif record.attribute and record.field and not record.inner_field:
                attrs[attr]='record.' + record.field.name
            elif record.attribute and record.inner_field and record.field:
                attrs[attr]='record.' + record.field.name+ '.' + record.inner_field.name
            elif not record.attribute and record.value:
                body = record.value
            elif not record.attribute and record.field and not record.inner_field:
                body = 'record.' + record.field.name
            elif not record.attribute and record.field and record.inner_field:
                body = 'record.' + record.field.name + '.' + record.inner_field.name

            root_node = ET.Element(tag,attrs)
                        # call generate_node ->tag tree
            if body != '':
                root_node.append(ET.Element('t',{'t-esc': body}))

            for tag_child in record.addenda_tag_childs_ids:
                root_node.append(ET.fromstring(tag_child.preview))
            ET.indent(root_node, '    ')
            if attr and value == '':
                value = 'value'

            record.preview = ET.tostring(root_node,pretty_print=True)


    