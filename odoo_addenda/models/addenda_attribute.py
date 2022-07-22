from odoo import models, fields, api, _
from lxml import etree


class AddendaAttribute(models.Model):
    _name = 'addenda.attribute'
    _description = 'Addenda attributes'

    addenda_tag_id = fields.Many2one(
        comodel_name='addenda.tag', string='Addenda tag')
    addenda_node_id = fields.Many2one(
        comodel_name='addenda.node', string='Addenda node')
    attribute = fields.Char(string='Attribute', help=_(
        'Name of the attribute of the new tag'))
    value = fields.Char(string='Attribute Value', help=_(
        'Value of the attribute of the new tag'))
    field = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'many2one', 'monetary', 'integer', 'boolean', 'date', 'datetime'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_('To select one fild, it only will appear if the user select one one2many field in the field fields'), comodel_name='ir.model.fields')
    field_type = fields.Char(compute='_compute_field_type', default='')

    attribute_options = fields.Selection(
        string='Attribute options', help=_('Attributes of "reference node"'), selection=lambda self: self._compute_attribute_options())

    @api.onchange('field')
    def _compute_inner_fields(self):
        domain = {'inner_field': []}
        for record in self:
            print(record.addenda_node_id.nodes)
            if record.field:
                if record.field.ttype == 'many2one':
                    domain = {'inner_field': [
                        ('model', '=', record.field.relation), ('ttype', '!=', 'many2one')]}
        return {'domain': domain}

    @api.depends('field')
    def _compute_field_type(self):
        for record in self:
            record.field_type = record.field.ttype

    def _compute_attribute_options(self):
        for record in self:
            print(record.addenda_node_id.nodes)
        print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
        print(self.addenda_node_id.nodes)
        if self.addenda_node_id.nodes:
            instance_cfdi = self.env.ref('l10n_mx_edi.cfdiv33')
            root = etree.fromstring(instance_cfdi.arch)
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
                        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
                        if(self.addenda_node_id.nodes == option):
                            for attr in child.attrib:
                                selection_vals.append(
                                    (attr.replace('t-att-', '')), attr.replace('t-att-', ''))
                            print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
                            print(selection_vals)
                            return selection_vals
                        path_list.append(child.tag.replace(
                            "{http://www.sat.gob.mx/cfd/3}", ""))
                        previous_child = child.tag
                except:
                    pass
