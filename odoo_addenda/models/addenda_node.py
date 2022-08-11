import xml.etree.ElementTree as ET
from lxml import etree

from odoo import api, fields, models


class AddendaNode(models.Model):
    _name = 'addenda.node'
    _description = 'Override the cfdiv33 template and add new nodes'

    nodes = fields.Selection(
        string='Reference Node', help=('Xml element that will serve as a reference for the new element'), selection=lambda self: self._selection_nodes(), required=True)
    position = fields.Selection(string='Position', help=('Where the new element is placed, relative to the reference element'), selection=[
        ('before', 'Before'), ('after', 'After'), ('inside', 'Inside'), ('attributes', 'Attributes')], required=True)
    addenda_id = fields.Many2one(
        string="Addenda", comodel_name="addenda.addenda")
    all_fields = fields.Many2one(
        string='Field', help=('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))])
    inner_field = fields.Many2one(
        string='Inner field', help=('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    inner_field_domain = fields.Char(
        string='Inner field domain', help=('Domain to filter the inner field'))
    field_type = fields.Char(compute='_compute_field_type', default='')
    path = fields.Text(string='Path', compute='_compute_path')
    attribute_value = fields.Char(string='Value of attribute', help=(
        'Value of the attribute of the new element'))
    cfdi_attributes_domain = fields.Char(
        string='cfdi_attributes domain', help=('Domain to filter the cfdi_attributes'))
    cfdi_attributes = fields.Many2one(
        comodel_name='addenda.cfdi.attributes', string='Attribute of reference node to edit')
    node_preview = fields.Text(
        string="Preview", compute='_compute_node_preview')
    addenda_tag_ids = fields.One2many(
        string='Addenda Tags', comodel_name='addenda.tag', inverse_name='addenda_node_id', help=('New addenda tags added'))

    @api.depends('all_fields')
    def _compute_field_type(self):
        for node in self:
            if node.all_fields:
                node.field_type = node.all_fields.ttype
            else:
                node.field_type = False

    @api.depends('nodes')
    def _compute_path(self):
        for node in self:
            if node.nodes:
                node.path = "".join([("{http://www.sat.gob.mx/cfd/3}", node.nodes.replace(
                    '/', '/{http://www.sat.gob.mx/cfd/3}')).replace('{http://www.sat.gob.mx/cfd/3}Comprobante', '.')])
            else:
                node.path = False

    @api.depends('nodes', 'attribute_value', 'cfdi_attributes', 'all_fields', 'inner_field', 'position', 'addenda_tag_ids')
    def _compute_node_preview(self):
        for nodes in self:
            node_expr = ''
            node = ''
            attribute_name = ''
            attribute_value = ''
            node_path = ''
            if nodes.nodes:
                node = nodes.nodes.split('/')[-1]
                node_expr = "//*[name()='%s']" % ("".join(['cfdi:', node]))
            if nodes.position and nodes.position == 'attributes':
                if nodes.cfdi_attributes:
                    attribute_name = 't-att-%s' % nodes.cfdi_attributes.name or ''

                if nodes.attribute_value:
                    attribute_value = ('format_string(%s)' %
                                       nodes.attribute_value)
                else:
                    attribute_value = ('line.%s' % nodes.all_fields.name) or '' if node == 'Concepto' and nodes.all_fields.model == 'account.move.line' else (
                        ('nodes.%s' % nodes.all_fields.name) if nodes.all_fields else '')
                    if nodes.inner_field:
                        attribute_value = "".join(
                            [attribute_value, '.%s' % nodes.inner_field.name])

                node_path = etree.Element(
                    "xpath", {'expr': node_expr, 'position': 'attributes'})
                attribute = etree.Element(
                    'attribute', {'name': attribute_name})
                attribute.text = attribute_value
                node_path.append(attribute)

                node_path = etree.tostring(node_path, pretty_print=True)
                nodes.node_preview = node_path
            elif nodes.position:
                node_path = etree.Element(
                    "xpath", {'expr': node_expr, 'position': nodes.position})
                if nodes.addenda_tag_ids:
                    for tag in nodes.addenda_tag_ids:
                        node_path.append(etree.fromstring(tag.preview))
                nodes.node_preview = etree.tostring(
                    node_path, pretty_print=True)
            else:
                nodes.node_preview = False

    def _selection_nodes(self):
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
                    option = "".join(["/".join(
                        path_list), "/", (child.tag.replace("{http://www.sat.gob.mx/cfd/3}", ""))])
                    selection_vals.append((option, option))
                    path_list.append(child.tag.replace(
                        "{http://www.sat.gob.mx/cfd/3}", ""))
                    previous_child = child.tag

            except:
                pass
        selection_vals = list(set(selection_vals))
        selection_vals.remove(('/Comprobante', '/Comprobante'))
        return selection_vals

    @api.onchange('all_fields')
    def _generate_inner_fields_domain(self):
        for node in self:
            if node.all_fields:
                node.inner_field_domain = node.all_fields.relation

    @api.onchange('nodes')
    def _generate_cfdi_attributes_domain(self):
        for node in self:
            if node.nodes:
                node.cfdi_attributes_domain = node.nodes

    @ api.onchange('nodes')
    def _generate_all_fields_domain(self):
        domain = {'all_fields': []}
        for node in self:
            # Clean attribute value
            node.cfdi_attributes = False
            if node.nodes == 'Comprobante/Conceptos/Concepto':
                domain = {'all_fields': [
                    ('model', 'in', ('account.move', 'account.move.line')), ('ttype', 'in', ('char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))]}
            else:
                domain = {'all_fields': [('model', '=', ('account.move')), ('ttype', 'in', (
                    'char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))]}
        return {'domain': domain}

    @api.onchange('position')
    def _position_onchange(self):
        for node in self:
            if(node.position == 'attributes'):
                node.addenda_tag_ids = False

            else:
                node.attribute_value = False
                node.cfdi_attributes = False
                node.inner_field = False
                node.all_fields = False

    @api.onchange('attribute_value')
    def delete_field(self):
        for node in self:
            if(node.attribute_value):
                node.all_fields = False
