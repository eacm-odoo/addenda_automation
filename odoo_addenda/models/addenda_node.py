from lxml.objectify import fromstring
import xml.etree.ElementTree as ET

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddendaNode(models.Model):
    _name = 'addenda.node'
    _description = 'Add nodes to addenda'

    # computed field name nodes
    nodes = fields.Selection(
        string='Reference Node', help=_('Xml element that will serve as a reference for the new element'), selection=lambda self: self._compute_nodes(), required=True)
    addenda_id = fields.Many2one(
        string="Addenda", comodel_name="addenda.addenda")
    all_fields = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'monetary', 'integer', 'boolean', 'date', 'datetime'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    field_type = fields.Char(compute='_compute_field_type', default='')
    path = fields.Text(string='Path', compute='_compute_path')
    attribute_options = fields.Text(
        string='Attributes options of reference node', help=_('Attributes of the node of the invoice xml'), compute='_compute_attributes', readonly=True)

    attribute_value = fields.Char(string='Value of attribute', help=_(
        'Value of the attribute of the new element'))
    cfdi_attributes = fields.Many2one(
        comodel_name='addenda.cfdi.attributes', string='Attribute of reference node to edit', required=True)

    @api.onchange('nodes')
    def _compute_cfdi_attributes(self):
        domain = {'cfdi_attributes': []}
        for record in self:
            domain = {'cfdi_attributes': [
                ('node', '=', record.nodes)]}
        return {'domain': domain}

    @api.onchange('attributes')
    def _validate_attributes(self):
        if self.attributes and self.attribute_options:
            list_of_attributes_options = self.attribute_options.split('\n')
            if self.attributes not in list_of_attributes_options:
                raise UserError(
                    _('The attribute you entered is not in the list of attributes options of the reference node'))

    @ api.onchange('nodes')
    def _compute_attributes(self):
        if self.nodes:
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
                        if parent_map[child].tag != previous_child:
                            if path_list:
                                while(path_list[-1] != parent_map[child].tag.replace(
                                        "{http://www.sat.gob.mx/cfd/3}", "")):
                                    path_list.pop()
                        option = "/".join(
                            path_list) + "/" + (child.tag.replace("{http://www.sat.gob.mx/cfd/3}", ""))
                        if(self.nodes == option):
                            for attr in child.attrib:
                                selection_vals.append(
                                    (attr.replace('t-att-', '')))
                            self.attribute_options = '\n'.join(selection_vals)
                            break
                        path_list.append(child.tag.replace(
                            "{http://www.sat.gob.mx/cfd/3}", ""))
                        previous_child = child.tag
                except:
                    pass

    @ api.onchange('nodes')
    def _compute_all_fields_domain(self):
        domain = {'all_fields': []}
        for record in self:
            if record.nodes == 'Comprobante/Conceptos/Concepto':
                domain = {'all_fields': [
                    ('model', 'in', ('account.move', 'account.move.line'))]}
            else:
                domain = {'all_fields': [('model', '=', ('account.move'))]}

        return {'domain': domain}

    @api.onchange('all_fields')
    def _compute_inner_fields(self):
        domain = {'inner_field': []}
        for record in self:
            if record.all_fields:
                if record.all_fields.ttype == 'many2one':
                    domain = {'inner_field': [
                        ('model', '=', record.all_fields.relation), ('ttype', '!=', 'many2one')]}
        return {'domain': domain}

    @ api.onchange('attribute_value')
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
