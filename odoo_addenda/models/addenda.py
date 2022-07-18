import xml.etree.ElementTree as ET
import os
import base64
from shutil import make_archive, rmtree
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


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
    state = fields.Selection(string="State", selection=[
        ('draft', "Draft"),
        ('done', "Done")
    ], default='draft')
    addenda_xml = fields.Text(string='Addenda XML', help=_('Addenda XML'))
    fields = fields.One2many(
        comodel_name='ir.model.fields', string="Fields", inverse_name='addenda_id')

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        self.generate_xml_fields(vals_list['fields'])
        if not(vals_list['is_customed_addenda']):
            root = etree.Element(vals_list['tag_name'])
            for tag in vals_list['addenda_tag_id']:
                xml_tree_tag = self.generate_tree_view(tag[2])
                root.append(xml_tree_tag)
            full_xml = self.get_xml(vals_list['name'], root)
            root_string = etree.tostring(root, pretty_print=True)
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
            res.write({'state': 'done', 'addenda_xml': etree.tostring(
                full_xml, pretty_print=True)})
        return res

    # Function to create the xml tree, given  tag_name and addenda_tag_id

    def generate_tree_view(self, addenda_tag):
        if type(addenda_tag) is list:
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

    def get_xml(self, name, root):
        xml = etree.Element("odoo")
        xml.set("noupdate", "0")
        template = etree.Element("template")
        template.set("id", "l10n_mx_edi_addenda_{}".format(
            name.lower().replace(' ', '_')))
        template.set("name", name)
        template.append(root)
        xml.append(template)
        record = etree.Element("record")
        record.set("id", "l10n_mx_edi_addenda_{}".format(
            name.lower().replace(' ', '_')))
        record.set("model", "ir.ui.view")
        field = etree.Element("field")
        field.set("name", "l10n_mx_edi_addenda_flag")
        field.text = "True"
        record.append(field)
        xml.append(record)
        return xml

    def action_export_zip(self):
        zip_file = self.create_directory(
            self.name, etree.fromstring(self.addenda_xml))
        attachment = self.env['ir.attachment'].create({
            'name': 'export_zip_module',
            'type': 'binary',
            'datas': zip_file,
            'mimetype': 'application/zip',
            'description': _('Zip file with the addenda and the new fields'),
        })
        rmtree(self.name)
        os.remove('addenda.zip')
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=1' % attachment['id']
        }

    def create_directory(sefl, name, xml):
        template = {
            'name': name,
            'sumary': 'Addenda created using addenda.addenda',
            'description': "",
            'author': 'Odoo PS',
            'category': 'Sales',
            'version': '15.0.1.0.0',
            'depends': ['sale', 'l10n_mx_edi'],
            'license': 'OPL-1',
            'data': [
                'views/addendas.xml',
            ],
        }

        os.makedirs(name+"/"+name+"/views")
        f = open(name+"/"+name+"/__manifest__.py", "w")
        f.write('{\n')
        for key, value in template.items():
            if(type(value) == list):
                f.write("'%s' : %s,\n" % (key, value))
            else:
                f.write("'%s' : '%s',\n" % (key, value))
        f.write('}')
        f.close()
        f = open(name+"/"+name+"/__init__.py", "w")
        f.close()
        tree = etree.ElementTree(xml)
        # save xml in the folder views
        tree.write(name+"/"+name+"/views/addendas.xml",
                   pretty_print=True, xml_declaration=True, encoding='utf-8')
        f.close()
        make_archive(
            'addenda',
            'zip',           # the archive format - or tar, bztar, gztar
            name)

        f = open("addenda.zip", "rb")
        bytes_content = f.read()

        bytes_content = base64.encodebytes(bytes_content)
        # rmtree("name")
        return bytes_content

    def generate_xml_fields(self, fields):
        root = ET.Element('data')
        for field in fields:
            model_name = self.env['ir.model'].search(
                [('id', '=', field[2]['model_id'])]).model
            record_node = self.generate_xml_element(
                'record', '', {'id': field[2]['field_description'], 'model': model_name})
            record_node.append(self.generate_xml_element(
                'field', field[2]['name'], {'name': 'name'}))
            record_node.append(self.generate_xml_element(
                'field', field[2]['field_description'], {'name': 'field_description'}))
            record_node.append(self.generate_xml_element(
                'field', field[2]['ttype'], {'name': 'ttype'}))
            record_node.append(self.generate_xml_element(
                'field', field[2]['model_id'], {'name': 'model_id'}))
            root.append(record_node)

        _logger.info(ET.tostring(root, xml_declaration=True))

        return root

    def generate_xml_element(self, name, text, attrs):
        new_element = ET.Element(name, attrs)
        new_element.text = str(text)
        return new_element
