import os
import base64
from shutil import make_archive, rmtree
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree


class AddendaAddenda(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name', required=True, help=_(
        'The name of the new customed addenda'))
    main_preview = fields.Text(string='Main Preview', help=_(
        'Main Preview'), compute='_compute_main_preview')

    nodes_ids = fields.One2many(
        comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
    is_customed_addenda = fields.Boolean(string='Customed Addenda', )
    is_expression = fields.Boolean(string='Is an expression', default=True)
    addenda_tag_id = fields.One2many(
        string='Addenda Tags', comodel_name='addenda.tag', inverse_name='addenda_addenda_id', help=_('New addenda tags added'))
    tag_name = fields.Char(string='Root Tag Name', required=True,
                           help=_('Name of the root tag tree'), default='Addenda')
    state = fields.Selection(string="State", selection=[
        ('draft', "Draft"),
        ('done', "Done")
    ], default='draft')
    addenda_xml = fields.Text(string='Addenda XML', help=_('Addenda XML'))
    addenda_expression = fields.Text(
        string='Addenda Expression', help=_('Addenda Expression'))
    addenda_fields_xml = fields.Text(
        string='Addenda Fields XML', help=_('Addenda Fields XML'))
    ir_ui_view_id = fields.Many2one(
        string='ir.ui.view view of the addenda', comodel_name='ir.ui.view')
    fields = fields.One2many(
        comodel_name='ir.model.fields', string="Fields", inverse_name='addenda_id')

    @api.onchange('is_expression')
    def _is_expression_onchange(self):
        if self.is_expression:
            self.tag_name = 'Addenda'
            self.addenda_tag_id = False
        else:
            self.nodes_ids = False

    @api.onchange('is_customed_addenda')
    def _is_expression_onchange(self):
        if self.is_customed_addenda:
            self.tag_name = 'Addenda'
            self.addenda_tag_id = False
            self.addenda_expression = False
        else:
            self.nodes_ids = False

    @api.onchange('addenda_expression')
    def evalue_expression(self):
        if(self.addenda_expression):
            try:
                etree.fromstring(self.addenda_expression)
            except:
                raise UserError(_("invalid format for xml"))

    @api.onchange('tag_name', 'addenda_tag_id')
    def _compute_main_preview(self):
        for record in self:
            root_tag = record.tag_name.replace(' ', '_') or 'root'
            root = etree.Element(root_tag)

            for tag in record.addenda_tag_id:
                root.append(etree.fromstring(tag.preview))
            etree.indent(root, '    ')

            record.main_preview = etree.tostring(root, pretty_print=True)

    @api.onchange('nodes_ids')
    def _compute_nodes_preview(self):
        for record in self:
            if(record.nodes_ids):
                main_preview = etree.Element("data")
                for node in record.nodes_ids:
                    main_preview.append(etree.fromstring(node.node_preview))
                etree.indent(main_preview, '    ')
                record.main_preview = etree.tostring(
                    main_preview, pretty_print=True)

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if not(vals_list['is_customed_addenda']):
            if vals_list['is_expression'] and vals_list['addenda_expression'] not in [False, '']:
                root = etree.fromstring(vals_list['addenda_expression'])
            elif vals_list['is_expression'] and vals_list['addenda_expression'] in [False, '']:
                return res
            elif not(vals_list['is_expression']):
                root = etree.Element(vals_list['tag_name'].replace(' ', '_'))
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

        else:
            new_fields_xml = self.generate_xml_fields(vals_list['fields'])
            string_cfdi_xml = self._generate_and_extend_cfdi(
                vals_list['nodes_ids'])
            full_xml = self.get_inherit_xml(
                vals_list['name'], etree.fromstring(string_cfdi_xml))
            cfdiv33 = self.env.ref(
                'l10n_mx_edi.cfdiv33')
            ir_ui_view = self.env['ir.ui.view'].create({
                'name': vals_list['name'],
                'type': 'qweb',
                'arch': string_cfdi_xml,
                'active': True,
                'inherit_id': cfdiv33.id,
                'model': False,
                'priority': 16,
                'arch_base': string_cfdi_xml,
                'arch_db': string_cfdi_xml,
                'arch_fs': False,
                'mode': 'extension',
            })
            res.write({'state': 'done',
                       'addenda_xml': etree.tostring(full_xml, pretty_print=True),
                       'addenda_fields_xml': etree.tostring(new_fields_xml, pretty_print=True),
                       'ir_ui_view_id': ir_ui_view.id})

        return res

    # override write function
    def write(self, vals):
        res = super().write(vals)
        instance = self.env['addenda.addenda'].browse(self.id)
        is_customed_addenda = (vals['is_customed_addenda'] if 'is_customed_addenda' in vals.keys(
        ) else False) or instance.is_customed_addenda
        fields = (vals['fields'] if 'fields' in vals.keys(
        ) else False) or instance.fields
        if not(is_customed_addenda):
            is_expression = (vals['is_expression'] if 'is_expression' in vals.keys(
            ) else False) or instance.is_expression
            addenda_expression = (vals['addenda_expression'] if 'addenda_expression' in vals.keys(
            ) else False) or instance.addenda_expression
            if is_expression and addenda_expression not in [False, '']:
                root = etree.fromstring(addenda_expression)
            elif is_expression and addenda_expression in [False, '']:
                vals['state'] = 'draft'
                res = super().write(vals)
                return res
            elif not(is_expression):
                root = etree.Element(instance.tag_name.replace(' ', '_'))
                for tag in instance.addenda_tag_id:
                    xml_tree_tag = self.generate_tree_view(tag)
                    root.append(xml_tree_tag)
            full_xml = self.get_xml(instance.name, root)
            root_string = etree.tostring(root, pretty_print=True)
            instance.ir_ui_view_id.write({
                'mode': 'primary',
                'inherit_id': False,
                'arch': root_string,
                'arch_db': root_string,
                'arch_base': root_string,
                'l10n_mx_edi_addenda_flag': True,
            })
            if fields:
                new_fields_xml = self.generate_xml_fields(fields, True)
                vals['addenda_fields_xml'] = etree.tostring(
                    new_fields_xml, pretty_print=True)
            vals['addenda_xml'] = etree.tostring(full_xml, pretty_print=True)
            # remove fields from vals
            vals.pop('fields', None)
            vals.pop('addenda_tag_id', None)
            vals['state'] = 'done'
            res = super().write(vals)
        else:
            nodes = instance.nodes_ids
            name = (vals['name'] if 'name' in vals.keys(
            ) else False) or instance.name
            if not nodes:
                vals['state'] = 'draft'
                res = super().write(vals)
                return res
            else:
                string_cfdi_xml = self._generate_and_extend_cfdi(nodes)
                full_xml = self.get_inherit_xml(
                    name, etree.fromstring(string_cfdi_xml))
                vals['addenda_xml'] = etree.tostring(
                    full_xml, pretty_print=True)
                cfdiv33 = self.env.ref(
                    'l10n_mx_edi.cfdiv33')
                instance.ir_ui_view_id.write({
                    'inherit_id': cfdiv33.id,
                    'mode': 'extension',
                    'l10n_mx_edi_addenda_flag': False,
                    'arch': string_cfdi_xml,
                    'arch_db': string_cfdi_xml,
                    'arch_base': string_cfdi_xml,
                })
            if fields:
                new_fields_xml = self.generate_xml_fields(fields, True)
                vals['addenda_fields_xml'] = etree.tostring(
                    new_fields_xml, pretty_print=True)
            # remove fields from vals
            vals.pop('fields', None)
            vals.pop('nodes_ids', None)
            vals['state'] = 'done'
            res = super().write(vals)
        return res

    # Function to create the xml tree, given  tag_name and addenda_tag_id
    def generate_tree_view(self, addenda_tag):
        if type(addenda_tag) is list:
            addenda_tag = addenda_tag[2]
            parent_node = etree.Element(
                addenda_tag['tag_name'].replace(' ', '_'))
        else:
            parent_node = etree.Element(
                addenda_tag['tag_name'].replace(' ', '_'))
        if addenda_tag['addenda_tag_childs_ids']:
            for child in addenda_tag['addenda_tag_childs_ids']:
                child_node = self.generate_tree_view(child)
                parent_node.append(child_node)
        if(addenda_tag['value']):
            parent_node.text = addenda_tag['value']
        if(addenda_tag['attribute_ids']):
            for attribute in addenda_tag['attribute_ids']:
                if(type(attribute) is list):
                    attribute = attribute[2]
                if(attribute['value']):
                    parent_node.set(attribute['attribute'], attribute['value'])
                elif(attribute['field'] and not attribute['value'] and not attribute['inner_field']):
                    parent_node.set("t-att-{}".format(attribute['attribute']),
                                    "record.{}".format(self.get_field_name(attribute['field'])))
                elif(attribute['field'] and attribute['inner_field']):
                    parent_node.set("t-att-{}".format(attribute['attribute']),
                                    "record.{}.{}".format(self.get_field_name(attribute['field']), self.get_field_name(attribute['inner_field'])))
        if(not addenda_tag['value'] and addenda_tag['field'] and not addenda_tag['inner_field']):
            t = etree.Element('t')
            t.set(
                "t-esc", "record.{}".format(self.get_field_name(addenda_tag['field'])))
            parent_node.append(t)
        if(not addenda_tag['value'] and addenda_tag['field'] and addenda_tag['inner_field']):
            t = etree.Element('t')
            t.set(
                "t-esc", "record.{}.{}".format(self.get_field_name(addenda_tag['field']), self.get_field_name(addenda_tag['inner_field'])))
            parent_node.append(t)
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

    def get_inherit_xml(self, name, root):
        xml = etree.Element("odoo")
        xml.set("noupdate", "0")
        template = etree.Element("template")
        template.set("id", "cfdiv33_inherit_{}".format(
            name.lower().replace(' ', '_')))
        template.set('inherit_id', "l10n_mx_edi.cfdiv33")
        for element in list(root):
            template.append(element)
        xml.append(template)
        return xml

    def action_export_zip(self):
        zip_file = self.create_directory(
            self.name, etree.fromstring(self.addenda_xml), etree.fromstring(self.addenda_fields_xml), self.is_customed_addenda)
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

    def create_directory(self, name, xml, fields, is_customed_addenda):
        name_view_file = "addenda" if not is_customed_addenda else "cfdiv33_inherit"
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
                'views/' + name_view_file + '.xml',
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
        tree.write(name+"/"+name+"/views/" + name_view_file + ".xml",
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

    def generate_xml_fields(self, fields, write=False):
        root = etree.Element('odoo')
        for field in fields:
            if type(field) != list:
                field = [0, 2, field]
                model_name = field[2].model
            elif write:
                instance_field = self.env['ir.model.fields'].browse(field[1])
                field = [0, 2, instance_field]
                model_name = self.env['ir.model'].search(
                    [('id', '=', int(field[2]['model_id']))]).model
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
            xml_field = etree.Element("field")
            xml_field.set("name", 'required')
            xml_field.text = str(field[2]['required'])
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'readonly')
            xml_field.text = str(field[2]['readonly'])
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'store')
            xml_field.text = str(field[2]['store'])
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'index')
            xml_field.text = str(field[2]['index'])
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'copied')
            xml_field.text = str(field[2]['copied'])
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'translate')
            xml_field.text = str(field[2]['translate'])
            record.append(xml_field)
            root.append(record)
        return root

    def _generate_and_extend_cfdi(self, nodes):
        path_extend = etree.Element("data")
        path_extend.set("inherit_id", "l10n_mx_edi.cfdiv33")
        for node in nodes:
            if(type(node) == list):
                node = node[2]
            path = "//*[name()='cfdi:" + \
                node['nodes'].split('/')[-1] + "']"
            if(type(node['cfdi_attributes']) == int):
                instance = self.env['addenda.cfdi.attributes'].browse(
                    node['cfdi_attributes'])
            else:
                instance = node['cfdi_attributes']
            if(type(node['all_fields']) == int):
                all_fields = self.env['ir.model.fields'].browse(
                    node['all_fields'])
            else:
                all_fields = node['all_fields']
            if(type(node['inner_field']) == int):
                inner_field = self.env['ir.model.fields'].browse(
                    node['inner_field'])
            else:
                inner_field = node['inner_field']
            if(node['addenda_tag_ids']):
                xpath = etree.Element("xpath")
                xpath.set("expr", path)
                xpath.set("position", node['position'])
                for tag in node['addenda_tag_ids']:
                    xml = self.generate_tree_view(tag)
                    xpath.append(xml)
                path_extend.append(xpath)
            else:
                xpath = etree.Element("xpath")
                xpath.set("expr", path)
                xpath.set("position", "attributes")
                attr = etree.Element("attribute")
                attr.set("name", "t-att-" + instance.name)
                if(node['attribute_value']):
                    attr.text = "format_string('" + node['attribute_value'] + \
                        "') or " + instance.value
                elif(all_fields and not inner_field):
                    if(all_fields.model == 'account.move.line'):
                        attr.text = "line." + \
                            self.get_field_name(all_fields) + \
                            " or (" + instance.value + ")"
                    else:
                        attr.text = "record." + \
                            self.get_field_name(all_fields) + \
                            " or (" + instance.value + ")"
                elif(inner_field and all_fields):
                    if(all_fields.model == 'account.move.line'):
                        attr.text = "line." + self.get_field_name(all_fields) + "." + self.get_field_name(
                            inner_field) + " or (" + instance.value + ")"
                    else:
                        attr.text = "record." + self.get_field_name(all_fields) + "." + self.get_field_name(
                            inner_field) + " or (" + instance.value + ")"
                xpath.append(attr)
                path_extend.append(xpath)
        path_extend = etree.tostring(
            path_extend, pretty_print=True, encoding='utf-8')
        return path_extend
