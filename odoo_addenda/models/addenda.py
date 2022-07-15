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
            for tag in res.addenda_tag_id:
                child_tag = self.generate_tree(tag)
                root.append(child_tag)
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

    def generate_tree(self, addenda_tag):
        parent_node = etree.Element(addenda_tag.tag_name)
        if addenda_tag.addenda_tag_childs_ids:
            for child in addenda_tag.addenda_tag_childs_ids:
                child_node = self.generate_node(child)
                parent_node.append(child_node)

        return parent_node
