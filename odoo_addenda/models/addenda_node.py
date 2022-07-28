from lxml.objectify import fromstring
import xml.etree.ElementTree as ET
from lxml import etree
import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


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
    field_type = fields.Char(compute='_compute_field_type', default='')
    path = fields.Text(string='Path', compute='_compute_path')

    attribute_value = fields.Char(string='Value of attribute', help=_(
        'Value of the attribute of the new element'))
    cfdi_attributes = fields.Many2one(
        comodel_name='addenda.cfdi.attributes', string='Attribute of reference node to edit')
    node_preview = fields.Text(readonly=True, compute='_compute_node_preview')
    attribute_pattern = fields.Char(string='Pattern', help=_(
        'Pattern to validate the attribute value'), compute='_compute_attribute_pattern')

    addenda_tag_ids = fields.One2many(
        string='Addenda Tags', comodel_name='addenda.tag', inverse_name='addenda_node_id', help=_('New addenda tags added'))

    @api.onchange('position')
    def _position_onchange(self):
        for record in self:
            if(record.position == 'attributes'):
                record.addenda_tag_ids = False
            else:
                record.attribute_value = False
                record.attribute_pattern = False
                record.cfdi_attributes = False
                record.inner_field = False
                record.all_fields = False

    @api.onchange('cfdi_attributes')
    def _compute_attribute_pattern(self):
        if self.cfdi_attributes and self.cfdi_attributes.pattern:
            self.attribute_pattern = self.cfdi_attributes.pattern
        else:
            self.attribute_pattern = False

    @api.onchange('nodes', 'attribute_value', 'cfdi_attributes', 'all_fields')
    def _compute_node_preview(self):
        for record in self:
            node_expr = ''
            attribute_name = ''
            attribute_value = ''

            if record.nodes:
                node = record.nodes.split('/')[-1]
                node_expr = "//*[name()='%s']" % ('cfdi:'+node)
            if record.cfdi_attributes:
                attribute_name = 't-att-%s' % record.cfdi_attributes.name or ''
                attribute_value = (record.attribute_value or (
                    'record.name or (%s)' % record.all_fields.name)) or ''

            node_path = etree.Element("xpath", {'expr': node_expr})
            attribute = etree.Element('attribute', {'name': attribute_name})
            attribute.text = attribute_value
            node_path.append(attribute)

            node_path = etree.tostring(node_path, pretty_print=True)

            record.node_preview = node_path

    @api.onchange('nodes')
    def _compute_cfdi_attributes(self):
        for record in self:
            domain = {'cfdi_attributes': [
                ('node', '=', record.nodes)]}
        return {'domain': domain}

    @ api.onchange('nodes')
    def _compute_all_fields_domain(self):
        domain = {'all_fields': []}
        for record in self:
            if record.nodes == 'Comprobante/Conceptos/Concepto':
                domain = {'all_fields': [
                    ('model', 'in', ('account.move', 'account.move.line')), ('ttype', 'in', ('char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))]}
            else:
                domain = {'all_fields': [('model', '=', ('account.move')), ('ttype', 'in', (
                    'char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime', 'many2one'))]}

        return {'domain': domain}

    @api.onchange('all_fields')
    def _compute_inner_fields(self):
        domain = {'inner_field': []}
        for record in self:
            if record.all_fields:
                if record.all_fields.ttype == 'many2one':
                    domain = {'inner_field': [
                        ('model', '=', record.all_fields.relation), ('ttype', '!=', 'many2one'), ('ttype', '!=', 'many2many'), ('ttype', '!=', 'one2many')]}
        return {'domain': domain}

    @api.onchange('attribute_value')
    def delete_field(self):
        for node in self:
            if(node.attribute_value):
                node.all_fields = False

    @api.onchange('attribute_value')
    @api.constrains('attribute_value')
    def _check_value_with_pattern(self):
        for record in self:
            if record.cfdi_attributes.pattern and record.attribute_value:
                pattern = re.compile(record.cfdi_attributes.pattern)
                if not pattern.match(record.attribute_value):
                    record.attribute_value = ''
                    raise ValidationError(
                        _('The value of the attribute is not valid, the pattern is %s') % record.cfdi_attributes.pattern)

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
                    if(len(child.attrib) > 0):
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
        selection_vals.remove(
            ('Comprobante/CfdiRelacionados', 'Comprobante/CfdiRelacionados'))
        selection_vals.remove(('Comprobante/CfdiRelacionados/CfdiRelacionado',
                              'Comprobante/CfdiRelacionados/CfdiRelacionado'))
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
