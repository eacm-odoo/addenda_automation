from logging import root
from xml.etree.ElementTree import QName
from lxml import etree as ET

from odoo import models, fields, api, _


class AddendaTag(models.Model):
    _name = 'addenda.tag'
    _description = 'Add many tags to node or anorther tag in addenda'

    addenda_node_id = fields.Many2one(
        string='Addenda Node', comodel_name='addenda.node')
    addenda_addenda_id = fields.Many2one(
        string='Addenda Addenda', comodel_name='addenda.addenda')
    addenda_tag_childs_ids = fields.One2many(
        comodel_name='addenda.tag', string='Addenda Tag Childs', inverse_name='addenda_tag_id', help=('New elements added inside this tag/element'))
    addenda_tag_id = fields.Many2one(
        string='Addenda tag', comodel_name='addenda.tag')
    tag_name = fields.Char(string='Tag Name', required=True,
                           help=('Name of the new tag/element'))
    attribute_ids = fields.One2many(
        comodel_name='addenda.attribute', string='Attributes', inverse_name='addenda_tag_id', help=('Attributes of the new tag/element'))
    value = fields.Char(string='Value', help=(
        'Value of the attribute of the new element'))
    field = fields.Many2one(
        string='Field', help=('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field = fields.Many2one(
        string='Inner field', help=('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    inner_field_domain = fields.Char(
        string='Inner field domain', help=('Domain to filter the inner field'))
    preview = fields.Text(store=False, string='Preview',
                          readonly=True, compute='_compute_preview', help=('A preview to hel the user to create the xml'))
    namespace = fields.Char(
        string='Namespace Prefix', help=('Namespace Prefix of the Addenda, helps to identify the nodes'))
    namespace_value = fields.Char(
        string='Namespace Value', help=('Namespace Value of the Addenda, helps to identify the nodes'))

    field_type = fields.Char(compute='_compute_field_type', default='')
    len_tag_childs = fields.Integer(compute='_compute_len_child_tags')

    @api.depends('addenda_tag_childs_ids')
    def _compute_len_child_tags(self):
        if(self.addenda_tag_childs_ids):
            self.len_tag_childs = len(self.addenda_tag_childs_ids)
        else:
            self.len_tag_childs = False

    @api.depends('field')
    def _compute_field_type(self):
        for tag in self:
            if tag.field:
                tag.field_type = tag.field.ttype
            else:
                tag.field_type = False

    @api.depends('tag_name', 'attribute_ids', 'value', 'field', 'addenda_tag_childs_ids', 'inner_field')
    def _compute_preview(self):
        for tags in self:
            if(tags.tag_name):
                tag = tags.tag_name.replace(' ', '_')
            else:
                tag = 'TagName'
            body = ''
            tags.preview = ''
            attrs = {}
            t_foreach = False
            if tags.attribute_ids:
                attrs = tags._set_tag_preview_attrs(tags,attrs)
            if tags.value:
                body = tags.value
            elif tags.field and not tags.inner_field:
                t_foreach,body=tags._set_preview_fields_no_inner(tags,t_foreach,body)
            elif tags.field and tags.inner_field:
                t_foreach,body=tags._set_preview_fields_inner(tags,t_foreach,body)
            if t_foreach:
                tags.preview = ET.tostring(t_foreach, pretty_print=True)
            else:
                root_node=ET.Element(tag,attrs)
                # call generate_node ->tag tree
                if body != '':
                    root_node.append(ET.Element('t', {'t-esc': body}))

                for tag_child in tags.addenda_tag_childs_ids:
                    root_node.append(ET.fromstring(tag_child.preview))
                ET.indent(root_node, '    ')

                tags.preview = ET.tostring(
                    root_node, encoding='unicode', pretty_print=True)

    def _set_preview_fields_inner(self,tags,t_foreach,body):
        if tags.field.ttype in ('one2many', 'many2many'):
            t_foreach = ET.Element(
                't', {'t-foreach': tags.field.name, 't-as': 'l'})
            tag_node = ET.Element(tags)
            t = ET.Element(
                't', {'t-esc': "".join(['l.', tags.inner_field.name])})
            tag_node.append(t)
            t_foreach.append(tag_node)
        else:
            body = "".join(['record.', tags.field.name, '.' , tags.inner_field.name])
        return t_foreach,body
    
    def _set_preview_fields_no_inner(self,tags,t_foreach,body):
        if tags.field.ttype in ('one2many', 'many2many'):
            t_foreach = ET.Element(
                't', {'t-foreach': tags.field.name, 't-as': 'l'})
            tag_node = ET.Element(tags)
            t_foreach.append(tag_node)
        else:
            body = "".join(['record.', tags.field.name])
        return t_foreach,body
    
    def _set_tag_preview_attrs(self,tags,attrs):
        for attr_record in tags.attribute_ids:
            if attr_record.value:
                attrs["".join(['t-att-',attr_record.attribute])] = attr_record.value
            elif attr_record.field and not attr_record.inner_field:
                attrs["".join(['t-att-', attr_record.attribute])] = "".join(['record.', attr_record.field.name])
            elif attr_record.inner_field and attr_record.field:
                attrs["".join(['t-att-', attr_record.attribute])] = "".join(['record.',
                    attr_record.field.name, '.', attr_record.inner_field.name])
        return attrs
    
    @api.onchange('field')
    def _compute_inner_fields_domain(self):
        for tag in self:
            if tag.field:
                tag.inner_field_domain = tag.field.relation

    @api.onchange('addenda_tag_childs_ids')
    def _child_ids_attribute_onchange(self):
        for tag in self:
            if (len(tag.addenda_tag_childs_ids) > 0):
                tag.field = False
                tag.inner_field = False
                tag.value = False

    @api.onchange('value')
    def _value_onchange(self):
        for tag in self:
            if tag.value:
                tag.field = False
                tag.inner_field = False
