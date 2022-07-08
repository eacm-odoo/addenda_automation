from lxml.objectify import fromstring
import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AddendaNode(models.Model):
    _name = 'addenda.node'
    _description = 'Add nodes to addenda'

    # computed field name nodes
    nodes = fields.Selection(
        string='Nodes', selection=lambda self: self._compute_nodes(), required=True)
    position = fields.Selection(string='Position', selection=[
        ('before', 'Before'), ('after', 'After'), ('inside', 'Inside'), ('attributes', 'Attributes')], required=True)
    addenda_id = fields.Many2one(
        string="Addenda", comodel_name="addenda.addenda")
    expression = fields.Text(string='Expression')
    all_models = fields.Many2one(
        string='Models', comodel_name='ir.model')
    all_fields = fields.Many2one(
        string='Fields', comodel_name='ir.model.fields', domain=[('model_id', '=', all_models)])

    @api.onchange('expression')
    def evalue_expression(self):
        for node in self:
            if(node.expression):
                try:
                    ET.fromstring(node.expression)
                except:
                    raise UserError(_("invalid format for xml"))
                    
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
        return selection_vals
