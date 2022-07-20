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
    addenda_fields_xml = fields.Text(
        string='Addenda Fields XML', help=_('Addenda Fields XML'))
    fields = fields.One2many(
        comodel_name='ir.model.fields', string="Fields", inverse_name='addenda_id')

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
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
            new_fields_xml = self.generate_xml_fields(vals_list['fields'])
            res.write({'state': 'done',
                       'addenda_xml': etree.tostring(full_xml, pretty_print=True),
                       'addenda_fields_xml': etree.tostring(new_fields_xml, pretty_print=True),
                       'ir_ui_view_id': ir_ui_view.id})
        return res

    # override write function

    def write(self, vals):
        res = super().write(vals)
        instance = self.env['addenda.addenda'].browse(self.id)
        if not(instance.is_customed_addenda):
            root = etree.Element(instance.tag_name)
            for tag in instance.addenda_tag_id:
                xml_tree_tag = self.generate_tree_view(tag)
                root.append(xml_tree_tag)
            full_xml = self.get_xml(instance.name, root)
            root_string = etree.tostring(root, pretty_print=True)
            instance.ir_ui_view_id.write({
                'arch': root_string,
                'arch_db': root_string,
                'arch_base': root_string,
            })
            if instance.fields:
                new_fields_xml = self.generate_xml_fields(instance.fields)
                vals['addenda_fields_xml'] = etree.tostring(
                    new_fields_xml, pretty_print=True)

            vals['addenda_xml'] = etree.tostring(full_xml, pretty_print=True)
            # remove fields from vals
            vals.pop('fields', None)
            res = super().write(vals)
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
        if type(field_id) is int:
            return self.env['ir.model.fields'].browse(field_id).name
        else:
            return field_id.name

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
            self.name, etree.fromstring(self.addenda_xml), etree.fromstring(self.addenda_fields_xml))
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

    def create_directory(self, name, xml, fields):
        template = {
            'name': name,
            'sumary': 'Addenda created using addenda.addenda',
            'description': "",
            'author': 'Odoo PS',
            'category': 'Sales',
            'version': '15.0.1.0.0',
            'depends': ['l10n_mx_edi'],
            'license': 'OPL-1',
            'data': [
                'views/addendas.xml',
            ],
        }

        os.makedirs(name+"/"+name+"/views")
        if(len(fields) > 0):
            os.mkdir(name+"/"+name+"/data")
            tree = etree.ElementTree(fields)
            tree.write(name+"/"+name+"/data/addenda_fields.xml",
                       pretty_print=True, xml_declaration=True, encoding='utf-8')
            template['data'].append('data/addenda_fields.xml')
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
        root = etree.Element('odoo')
        for field in fields:
            if type(field) != list:
                field = [0, 2, field]
                model_name = field[2].model
            else:
                model_name = self.env['ir.model'].search(
                    [('id', '=', field[2]['model_id'])]).model
            model_data = self.env['ir.model.data'].search(
                [('model', '=', model_name)], limit=1)
            external_id = model_data.module + '.model_' + \
                (model_data.model.replace('.', '_'))
            record = etree.Element("record")
            record.set("id", field[2]['field_description'].replace(' ', '_'))
            record.set("model", "ir.model.fields")
            xml_field = etree.Element("field")
            xml_field.set("name", 'name')
            xml_field.text = field[2]['name']
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'field_description')
            xml_field.text = field[2]['field_description']
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'model_id')
            xml_field.set("ref", external_id)
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'ttype')
            xml_field.text = field[2]['ttype']
            record.append(xml_field)
            root.append(record)
        return root

    def generate_xml_element(self, name, text, attrs):
        new_element = etree.Element(name, attrs)
        new_element.text = str(text)
        return new_element
