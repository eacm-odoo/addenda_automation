import string
from lxml.objectify import fromstring
import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddendaNode(models.Model):
    _name = 'addenda.node'
    _description = 'Add nodes to addenda'

    # computed field name nodes
    nodes = fields.Selection(
        string='Refernece Node', help=_('Xml element that will serve as a reference for the new element'), selection=lambda self: self._compute_nodes(), required=True)
    position = fields.Selection(string='Position', help=_('Where the new element is placed, relative to the reference element'), selection=[
        ('before', 'Before'), ('after', 'After'), ('inside', 'Inside'), ('attributes', 'Attributes')], required=True)
    addenda_id = fields.Many2one(
        string="Addenda", comodel_name="addenda.addenda")
    all_fields = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields', domain=[('model', '=', 'account.move')])
    path = fields.Text(string='Path', compute='_compute_path')

    tag_name = fields.Char(string='Root Tag name')
    attribute = fields.Char(string='Attribute')
    attribute_value = fields.Char(string='Value of attribute')

    addenda_tag_id = fields.One2many(
        string='Addenda Tag', comodel_name='addenda.tag', inverse_name='addenda_node_id')

   
    # validate if position = "attributes" set addenda_tag_id to False
    @api.onchange('position')
    def validate_position(self):
        for node in self:
            if(node.position == 'attributes'):
                node.addenda_tag_id = False

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
        selection_vals.append(
            ('Comprobante/Complemento', 'Comprobante/Complemento'))
        selection_vals.remove(('/Comprobante', '/Comprobante'))
        return selection_vals

    # compute the whole path of the node
    @api.depends('nodes')
    def _compute_path(self):
        for node in self:
            if(node.nodes):
                node.path = ("{http://www.sat.gob.mx/cfd/3}" + node.nodes.replace(
                    '/', '/{http://www.sat.gob.mx/cfd/3}')).replace('{http://www.sat.gob.mx/cfd/3}Comprobante', '.')
            else:
                node.path = False
