from lxml.objectify import fromstring
import xml.etree.ElementTree as ET
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
        string='Inner field', help=_(''), comodel_name='ir.model.fields')
    preview = fields.Text(store=False, string='Preview',
                          readonly=True, compute='_compute_preview')
    
    field_type=fields.Char(compute='_compute_field_type',default='')
    len_tag_childs= fields.Integer(compute='_compute_len_child_tags')
    
    @api.depends('addenda_tag_childs_ids')
    def _compute_len_child_tags(self):
        self.len_tag_childs=len(self.addenda_tag_childs_ids)
        
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
                record.field=False
                record.inner_field=False
                record.value=False
    
    
    @api.onchange('value')
    def _value_onchange(self):
        for record in self:
            if record.value:
                record.field=False
                record.inner_field=False
                
                    

    @api.depends('tag_name', 'attribute', 'value', 'field', 'addenda_tag_childs_ids', 'inner_field')
    def _compute_preview(self):
        tag = self.tag_name or 'Tag name'
        attr = ('t-att-' + self.attribute + '=') if self.attribute else ''
        value = ''
        body = ''
        self.preview = ''

        if self.value and self.attribute:
            value = '"' + self.value + '"'
        elif self.attribute and self.field and not self.inner_field:
            value = '"record.' + self.field.name + '"'
        elif self.attribute and self.inner_field and self.field:
            value = '"record.' + self.field.name + '.' + self.inner_field.name + '"'
        elif not self.attribute and self.value:
            body = '\n\t' + self.value
        elif not self.attribute and self.field and not self.inner_field:
            body = '\n\t' + '<t t-esc="record.' + self.field.name + '"/>'
        elif not self.attribute and self.field and self.inner_field:
            body = '\n\t' + '<t t-esc="record.' + self.field.name + \
                '.' + self.inner_field.name + '"/>'

        for tag_child in self.addenda_tag_childs_ids:
            tag_child = self.generate_preview_node(
                tag_child.tag_name, tag_child.attribute, tag_child.value, tag_child.field, tag_child.inner_field)
            body = body + '\n\t' + tag_child

        if attr and value == '':
            value = 'value'

        node = '<%s %s%s>%s\n</%s>' % (tag, attr, value, body, tag)
        self.preview = node

    def generate_preview_node(self, tag_name, attribute, value, field, inner_field):
        tag = tag_name or 'Tag name'
        attr = ('t-att-' + attribute + '=') if attribute else ''
        values = ''
        body = ''

        if value and attribute:
            values = '"' + value + '"'
        elif attribute and field and not inner_field:
            values = '"record.' + field.name + '"'
        elif attribute and inner_field and field:
            values = '"record.' + field.name + '.' + inner_field.name + '"'
        elif not attribute and value:
            body = '\n\t' + value
        elif not attribute and field and not inner_field:
            body = '\n\t' + '<t t-esc="record.' + field.name + '"/>'
        elif not attribute and field and inner_field:
            body = '\n\t' + '<t t-esc="record.' + field.name + '.' + inner_field.name + '"/>'

        node = '<%s %s%s>%s\n\t</%s>' % (tag, attr, values, body, tag)
        return node
