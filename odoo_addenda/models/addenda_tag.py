from lxml import etree as ET

from odoo import models, fields, api, _


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
    attribute_ids = fields.One2many(
        comodel_name='addenda.attribute', string='Attributes', inverse_name='addenda_tag_id', help=_('Attributes of the new tag/element'))
    value = fields.Char(string='Value', help=_(
        'Value of the attribute of the new element'))
    field = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    inner_field_domain = fields.Char(
        string='Inner field domain', help=_('Domain to filter the inner field'))
    preview = fields.Text(store=False, string='Preview',
                          readonly=True, compute='_compute_preview', help=_('A preview to hel the user to create the xml'))

    field_type = fields.Char(compute='_compute_field_type', default='')
    len_tag_childs = fields.Integer(compute='_compute_len_child_tags')

    @api.depends('addenda_tag_childs_ids')
    def _compute_len_child_tags(self):
        self.len_tag_childs = len(self.addenda_tag_childs_ids)

    @api.depends('field')
    def _compute_field_type(self):
        for record in self:
            record.field_type = record.field.ttype

    @api.depends('tag_name', 'attribute_ids', 'value', 'field', 'addenda_tag_childs_ids', 'inner_field')
    def _compute_preview(self):
        for record in self:
            if(record.tag_name):
                tag = record.tag_name.replace(' ', '_')
            else:
                tag = 'TagName'
            body = ''
            record.preview = ''
            attrs = {}
            t_foreach = False
            if len(record.attribute_ids) > 0:
                for attr_record in record.attribute_ids:
                    if attr_record.value:
                        attrs['t-att-'+attr_record.attribute] = attr_record.value
                    elif attr_record.field and not attr_record.inner_field:
                        attrs['t-att-'+attr_record.attribute] = 'record.' + \
                            attr_record.field.name
                    elif attr_record.inner_field and attr_record.field:
                        attrs['t-att-'+attr_record.attribute] = 'record.' + \
                            attr_record.field.name + '.' + attr_record.inner_field.name

            if record.value:
                body = record.value
            elif record.field and not record.inner_field:
                if record.field.ttype in ('one2many', 'many2many'):
                    t_foreach = ET.Element(
                        't', {'t-foreach': record.field.name, 't-as': 'l'})
                    tag_node = ET.Element(tag)
                    t_foreach.append(tag_node)
                else:
                    body = 'record.' + record.field.name
            elif record.field and record.inner_field:
                if record.field.ttype in ('one2many', 'many2many'):
                    t_foreach = ET.Element(
                        't', {'t-foreach': record.field.name, 't-as': 'l'})
                    tag_node = ET.Element(tag)
                    t = ET.Element(
                        't', {'t-esc': 'l.' + record.inner_field.name})
                    tag_node.append(t)
                    t_foreach.append(tag_node)
                else:
                    body = 'record.' + record.field.name + '.' + record.inner_field.name
            if t_foreach:
                record.preview = ET.tostring(t_foreach, pretty_print=True)

            else:
                root_node = ET.Element(tag, attrs)

                # call generate_node ->tag tree
                if body != '':
                    root_node.append(ET.Element('t', {'t-esc': body}))

                for tag_child in record.addenda_tag_childs_ids:
                    root_node.append(ET.fromstring(tag_child.preview))
                ET.indent(root_node, '    ')

                record.preview = ET.tostring(
                    root_node, encoding='unicode', pretty_print=True)

    @api.onchange('field')
    def _compute_inner_fields_domain(self):
        for record in self:
            if record.field:
                record.inner_field_domain = record.field.relation

    @api.onchange('addenda_tag_childs_ids')
    def _child_ids_attribute_onchange(self):
        for record in self:
            if (len(record.addenda_tag_childs_ids) > 0):
                record.field = False
                record.inner_field = False
                record.value = False

    @api.onchange('value')
    def _value_onchange(self):
        for record in self:
            if record.value:
                record.field = False
                record.inner_field = False
