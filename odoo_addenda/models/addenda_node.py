import xml.etree.ElementTree as ET
from lxml import etree
from odoo import models, fields, api, _


class AddendaNode(models.Model):
    _name = 'addenda.node'
    _description = 'Add nodes to addenda'

    # computed field name nodes
    nodes = fields.Selection(
        string='Reference Node', help=_('Xml element that will serve as a reference for the new element'), selection=lambda self: self._compute_nodes(), required=True)
    position = fields.Selection(string='Position', help=_('Where the new element is placed, relative to the reference element'), selection=[
        ('before', 'Before'), ('after', 'After'), ('inside', 'Inside'), ('attributes', 'Attributes')], required=True)
    addenda_id = fields.Many2one(
        string="Addenda", comodel_name="addenda.addenda")
    all_fields = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    inner_field_domain = fields.Char(
        string='Inner field domain', help=_('Domain to filter the inner field'))
    field_type = fields.Char(compute='_compute_field_type', default='')
    path = fields.Text(string='Path', compute='_compute_path')
    attribute_value = fields.Char(string='Value of attribute', help=_(
        'Value of the attribute of the new element'))
    cfdi_attributes_domain = fields.Char(
        string='cfdi_attributes domain', help=_('Domain to filter the cfdi_attributes'))
    cfdi_attributes = fields.Many2one(
        comodel_name='addenda.cfdi.attributes', string='Attribute of reference node to edit')
    node_preview = fields.Text(string="Previw of the node", compute='_compute_node_preview')
    addenda_tag_ids = fields.One2many(
        string='Addenda Tags', comodel_name='addenda.tag', inverse_name='addenda_node_id', help=_('New addenda tags added'))

    @api.onchange('position')
    def _position_onchange(self):
        for record in self:
            if(record.position == 'attributes'):
                record.addenda_tag_ids = False
                
            else:
                record.attribute_value = False
                record.cfdi_attributes = False
                record.inner_field = False
                record.all_fields = False

    @api.onchange('all_fields')
    def _compute_inner_fields_domain(self):
        for record in self:
            if record.all_fields:
                record.inner_field_domain = record.all_fields.relation

    @api.onchange('nodes')
    def _compute_cfdi_attributes_domain(self):
        for record in self:
            if record.nodes:
                record.cfdi_attributes_domain = record.nodes

    @api.onchange('nodes', 'attribute_value', 'cfdi_attributes', 'all_fields', 'inner_field', 'position', 'addenda_tag_ids')
    def _compute_node_preview(self):
        for record in self:
            node_expr = ''
            node = ''
            attribute_name = ''
            attribute_value = ''
            node_path=''
            if record.nodes:
                node = record.nodes.split('/')[-1]
                node_expr = "//*[name()='%s']" % ('cfdi:'+node)
            if  record.position and record.position == 'attributes':
                if record.cfdi_attributes:
                    attribute_name = 't-att-%s' % record.cfdi_attributes.name or ''

                if record.attribute_value:
                    attribute_value = ('format_string(%s)' %
                                    record.attribute_value)
                else:
                    attribute_value = ('line.%s' % record.all_fields.name) or '' if node == 'Concepto' and record.all_fields.model == 'account.move.line' else (
                        ('record.%s' % record.all_fields.name) if record.all_fields else '')
                    if record.inner_field:
                        print(record.inner_field.name)
                        attribute_value += '.%s' % record.inner_field.name

                node_path = etree.Element("xpath", {'expr': node_expr, 'position': 'attributes'})
                attribute = etree.Element('attribute', {'name': attribute_name})
                attribute.text = attribute_value
                node_path.append(attribute)

                node_path = etree.tostring(node_path, pretty_print=True)
                record.node_preview = node_path
            elif record.position:
                node_path = etree.Element("xpath", {'expr': node_expr, 'position': record.position})
                if record.addenda_tag_ids:
                    for tag in record.addenda_tag_ids:
                        node_path.append(etree.fromstring(tag.preview))
                record.node_preview = etree.tostring(node_path, pretty_print=True)



    @ api.onchange('nodes')
    def _compute_all_fields_domain(self):
        domain = {'all_fields': []}
        for record in self:
            # Clean attribute value
            record.cfdi_attributes = False
            if record.nodes == 'Comprobante/Conceptos/Concepto':
                domain = {'all_fields': [
                    ('model', 'in', ('account.move', 'account.move.line')), ('ttype', 'in', ('char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))]}
            else:
                domain = {'all_fields': [('model', '=', ('account.move')), ('ttype', 'in', (
                    'char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))]}
        return {'domain': domain}

    @api.onchange('attribute_value')
    def delete_field(self):
        for node in self:
            if(node.attribute_value):
                node.all_fields = False

    # recover all the nodes of the cfdiv33 so the user can choose one
    def _compute_nodes(self):
        # use self.env.ref to get the xml file
        instance_cfdi = self.env.ref('l10n_mx_edi.cfdiv33')
        root = ET.fromstring(instance_cfdi.arch)
        parent_map = {c: p for p in root.iter()
                      for c in p}
        selection_vals = []
        path_list = []  # list of element's parents
        previous_child = None
        for child in root.iter():
            try:
                if child.tag == 't':
                    child.tag = parent_map[child].tag
                if(child.tag != parent_map[child].tag):
                    # if the parent is different from the previous one
                    if parent_map[child].tag != previous_child:
                        if path_list:
                            # remove the last element of the list
                            while(path_list[-1] != parent_map[child].tag.replace(
                                    "{http://www.sat.gob.mx/cfd/3}", "")):
                                path_list.pop()
                    option = "/".join(
                        path_list) + "/" + (child.tag.replace("{http://www.sat.gob.mx/cfd/3}", ""))
                    selection_vals.append((option, option))
                    path_list.append(child.tag.replace(
                        "{http://www.sat.gob.mx/cfd/3}", ""))
                    previous_child = child.tag

            except:
                pass
        selection_vals = list(set(selection_vals))
        selection_vals.remove(('/Comprobante', '/Comprobante'))
        return selection_vals

    @api.depends('all_fields')
    def _compute_field_type(self):
        for record in self:
            record.field_type = record.all_fields.ttype

    # compute the whole path of the node
    @ api.depends('nodes')
    def _compute_path(self):
        for node in self:
            if(node.nodes):
                node.path = ("{http://www.sat.gob.mx/cfd/3}" + node.nodes.replace(
                    '/', '/{http://www.sat.gob.mx/cfd/3}')).replace('{http://www.sat.gob.mx/cfd/3}Comprobante', '.')
            else:
                node.path = False
