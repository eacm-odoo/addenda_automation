import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree


class AddendaAddenda(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name', required=True, help=_(
        'The name of the new customed addenda'))
    nodes_ids = fields.One2many(
        comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
    is_customed_addenda = fields.Boolean(string='Customed Addenda', )
    addenda_tag_id = fields.One2many(
        string='Addenda Tags', comodel_name='addenda.tag', inverse_name='addenda_addenda_id', help=_('New addenda tags added'))
    tag_name = fields.Char(string='Root Tag Name', required=True,
                           help=_('Name of the root tag tree'))

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if not(vals_list['is_customed_addenda']):
            root = etree.Element(vals_list['tag_name'])
            for tag in vals_list['addenda_tag_id']:
                xml_tree_tag = self.generate_tree_view(tag[2])
                root.append(xml_tree_tag)
            root_string = etree.tostring(root, pretty_print=True)
            print(root_string)
            ir_ui_view = self.env['ir.ui.view'].create({
                'name': vals_list['name'],
                'type': 'qweb',
                'arch': root_string,
                'active': True,
                'inherit_id': False,
                'model': False,
                'priority': 16,
                'arch_base': root_string,
                'arch_db': root_string,
                'arch_fs': False,
                'mode': 'primary',
                'l10n_mx_edi_addenda_flag': True,
            })
        return res

    # Function to create the xml tree, given  tag_name and addenda_tag_id

    def generate_tree_view(self, addenda_tag):
        if type(addenda_tag) is list:
            print(addenda_tag)
            addenda_tag = addenda_tag[2]
            parent_node = etree.Element(addenda_tag['tag_name'])
        else:
            parent_node = etree.Element(addenda_tag['tag_name'])
        if addenda_tag['addenda_tag_childs_ids']:
            for child in addenda_tag['addenda_tag_childs_ids']:
                child_node = self.generate_tree_view(child)
                parent_node.append(child_node)
        if(addenda_tag['value'] and not addenda_tag['attribute']):
            parent_node.text = addenda_tag['value']
        elif(addenda_tag['value'] and addenda_tag['attribute']):
            parent_node.set(addenda_tag['attribute'], addenda_tag['value'])
        elif(not addenda_tag['attribute'] and not addenda_tag['value'] and addenda_tag['field'] and not addenda_tag['inner_field']):
            t = etree.Element('t')
            t.set(
                "t-esc", "record.{}".format(self.get_field_name(addenda_tag['field'])))
            parent_node.append(t)
        elif(not addenda_tag['attribute'] and not addenda_tag['value'] and addenda_tag['field'] and addenda_tag['inner_field']):
            t = etree.Element('t')
            t.set(
                "t-esc", "record.{}.{}".format(self.get_field_name(addenda_tag['field']), self.get_field_name(addenda_tag['inner_field'])))
            parent_node.append(t)
        elif(addenda_tag['attribute'] and not addenda_tag['value'] and addenda_tag['field'] and not addenda_tag['inner_field']):
            parent_node.set("t-att-{}".format(addenda_tag['attribute']),
                            "record.{}".format(self.get_field_name(addenda_tag['field'])))
        elif(addenda_tag['attribute'] and not addenda_tag['value'] and addenda_tag['field'] and addenda_tag['inner_field']):
            parent_node.set("t-att-{}".format(addenda_tag['attribute']),
                            "record.{}.{}".format(self.get_field_name(addenda_tag['field']), self.get_field_name(addenda_tag['inner_field'])))
        return parent_node

    def get_field_name(self, field_id):
        return self.env['ir.model.fields'].browse(field_id).name
