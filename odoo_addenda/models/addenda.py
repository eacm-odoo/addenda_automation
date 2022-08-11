import os
import base64
from shutil import make_archive, rmtree
from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AddendaAddenda(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name', required=True, help=(
        'The name of the new customed addenda'))
    main_preview = fields.Text(string='Main Preview', help=(
        'Main Preview'), compute='_compute_main_preview')
    node_main_preview = fields.Text(string='Main Preview of the nodes', help=(
        'Main Preview'), compute='_compute_nodes_preview')

    nodes_ids = fields.One2many(
        comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
    is_customed_addenda = fields.Boolean(string='Inherit CFDI template', help=(
        'Inherit the CFDI template and override it'))
    is_expression = fields.Boolean(string='Is an expression', default=True)
    addenda_tag_id = fields.One2many(
        string='Addenda Tags', comodel_name='addenda.tag', inverse_name='addenda_addenda_id', help=('New addenda tags added'))
    tag_name = fields.Char(string='Root Tag Name', required=True,
                           help=('Name of the root tag tree'), default='Addenda')
    namespace = fields.Char(
        string='Namespace Prefix', help=('Namespace Prefix of the Addenda, helps to identify the nodes'))
    namespace_value = fields.Char(
        string='Namespace Value', help=('Namespace Value of the Addenda, helps to identify the nodes'))

    state = fields.Selection(string="State", selection=[
        ('draft', "Draft"),
        ('done', "Done")
    ], default='draft')
    addenda_xml = fields.Text(string='Addenda XML', help=('Addenda XML'))
    addenda_expression = fields.Text(
        string='Addenda Expression', help=('Addenda Expression'))
    addenda_fields_xml = fields.Text(
        string='Addenda Fields XML', help=('Addenda Fields XML'))
    ir_ui_view_id = fields.Many2one(
        string='ir.ui.view view of the addenda', comodel_name='ir.ui.view')
    fields = fields.One2many(
        comodel_name='ir.model.fields', string="Fields", inverse_name='addenda_id')

    @api.depends('tag_name', 'addenda_tag_id')
    def _compute_main_preview(self):
        for addenda in self:
            root_tag = addenda.tag_name.replace(' ', '_') or 'root'
            root = etree.Element(root_tag)

            for tag in addenda.addenda_tag_id:
                root.append(etree.fromstring(tag.preview))
            etree.indent(root, '    ')

            addenda.main_preview = etree.tostring(root, pretty_print=True)

    @api.depends('nodes_ids')
    def _compute_nodes_preview(self):
        for addenda in self:
            if(addenda.nodes_ids):
                main_preview = etree.Element("data")
                for node in addenda.nodes_ids:
                    main_preview.append(etree.fromstring(node.node_preview))
                etree.indent(main_preview, '    ')
                addenda.node_main_preview = etree.tostring(
                    main_preview, pretty_print=True)
            else:
                addenda.node_main_preview = False

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

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if not(vals_list['is_customed_addenda']):
            if vals_list['is_expression'] and vals_list['addenda_expression'] not in [False, '']:
                root = etree.fromstring(vals_list['addenda_expression'])
            elif vals_list['is_expression'] and vals_list['addenda_expression'] in [False, '']:
                return res
            elif not(vals_list['is_expression']):
                if(vals_list['namespace']):
                    etree.register_namespace(
                        vals_list['namespace'], vals_list['namespace_value'])
                    root = etree.Element(etree.QName(
                        vals_list['namespace_value'], vals_list['tag_name'].replace(' ', '_')))
                else:
                    root = etree.Element(
                        vals_list['tag_name'].replace(' ', '_'))
                for tag in vals_list['addenda_tag_id']:
                    xml_tree_tag = self.generate_tree_view(
                        tag, vals_list['namespace_value'])
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
        is_customed_addenda = instance.is_customed_addenda
        fields = instance.fields
        if not(is_customed_addenda):
            is_expression = instance.is_expression
            addenda_expression = instance.addenda_expression
            if is_expression and addenda_expression not in [False, '']:
                root = etree.fromstring(addenda_expression)
            elif is_expression and addenda_expression in [False, '']:
                vals['state'] = 'draft'
                res = super().write(vals)
                return res
            elif not(is_expression):
                if(instance.namespace):
                    etree.register_namespace(
                        instance.namespace, instance.namespace_value)
                    root = etree.Element(etree.QName(
                        instance.namespace_value, instance.tag_name.replace(' ', '_')))
                else:
                    root = etree.Element(instance.tag_name.replace(' ', '_'))
                for tag in instance.addenda_tag_id:
                    xml_tree_tag = self.generate_tree_view(
                        tag, instance.namespace_value)
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
        rmtree(self.name.replace(' ', '_').replace('.', ''))
        os.remove('addenda.zip')
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=1' % attachment['id']
        }

    # Function to create the xml tree, given  tag_name and addenda_tag_id
    def generate_tree_view(self, addenda_tag, prefix):
        if type(addenda_tag) is list:
            addenda_tag = addenda_tag[2]
            if(prefix):
                parent_node = etree.Element(
                    etree.QName(prefix, addenda_tag['tag_name'].replace(' ', '_')))
            else:
                parent_node = etree.Element(
                    addenda_tag['tag_name'].replace(' ', '_'))
        elif type(addenda_tag) is int:
            addenda_tag = self.env['addenda.tag'].search_read(
                [('id', '=', addenda_tag)])[0]
            if(prefix):
                parent_node = etree.Element(
                    etree.QName(prefix, addenda_tag['tag_name'].replace(' ', '_')))
            else:
                parent_node = etree.Element(
                    addenda_tag['tag_name'].replace(' ', '_'))
        else:
            if(prefix):
                parent_node = etree.Element(
                    etree.QName(prefix, addenda_tag['tag_name'].replace(' ', '_')))
            else:
                parent_node = etree.Element(
                    addenda_tag['tag_name'].replace(' ', '_'))
        if addenda_tag['addenda_tag_childs_ids']:
            for child in addenda_tag['addenda_tag_childs_ids']:
                child_node = self.generate_tree_view(child, prefix)
                parent_node.append(child_node)
        if(addenda_tag['value']):
            parent_node.text = addenda_tag['value']
        if(addenda_tag['attribute_ids']):
            for attribute in addenda_tag['attribute_ids']:
                if(type(attribute) is list):
                    attribute = attribute[2]
                elif(type(attribute) is int):
                    attribute = self.env['addenda.attribute'].search_read(
                        [('id', '=', attribute)])[0]
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
        if(not addenda_tag['value'] and addenda_tag['field'] and self.get_field_type(addenda_tag['field']) in ('many2many', 'one2many') and addenda_tag['inner_field']):
            t = etree.Element('t')
            t.set(
                "t-foreach", "record.{}".format(self.get_field_name(addenda_tag['field'])))
            t.set("t-as", "l")
            t2 = etree.Element('t')
            t2.set(
                "t-esc", "l.{}".format(self.get_field_name(addenda_tag['inner_field'])))
            parent_node.append(t2)
            t.append(parent_node)
            parent_node = t
        elif(not addenda_tag['value'] and addenda_tag['field'] and addenda_tag['inner_field']):
            t = etree.Element('t')
            t.set(
                "t-esc", "record.{}.{}".format(self.get_field_name(addenda_tag['field']), self.get_field_name(addenda_tag['inner_field'])))
            parent_node.append(t)
        return parent_node

    def get_field_name(self, field_id):
        if type(field_id) is int:
            return self.env['ir.model.fields'].browse(field_id).name
        elif type(field_id) is tuple:
            return self.env['ir.model.fields'].browse(field_id[0]).name
        else:
            return field_id.name

    def get_field_type(self, field_id):
        if type(field_id) is int:
            return self.env['ir.model.fields'].browse(field_id).ttype
        elif type(field_id) is tuple:
            return self.env['ir.model.fields'].browse(field_id[0]).ttype
        else:
            return field_id.ttype

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

    def create_directory(self, name, xml, fields, is_customed_addenda):
        name = name.replace(' ', '_').replace('.', '')
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
                "".join(['views/', name_view_file, '.xml']),
            ],
        }

        os.makedirs("".join([name, "/", name, "/views"]))
        if(len(fields) > 0):
            os.mkdir("".join([name, "/", name, "/data"]))
            tree = etree.ElementTree(fields)
            tree.write("".join([name, "/", name, "/data/addenda_fields.xml"]),
                       pretty_print=True, xml_declaration=True, encoding='utf-8')
            template['data'].append('data/addenda_fields.xml')
        f = open("".join([name, "/", name, "/__manifest__.py"]), "w")
        f.write('{\n')
        for key, value in template.items():
            if(type(value) == list):
                f.write("'%s' : %s,\n" % (key, value))
            else:
                f.write("'%s' : '%s',\n" % (key, value))
        f.write('}')
        f.close()
        f = open("".join([name, "/", name, "/__init__.py"]), "w")
        f.close()
        tree = etree.ElementTree(xml)
        tree.write("".join([name, "/", name, "/views/", name_view_file, ".xml"]),
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
                if type(field) == int:
                    field = [0, 2, self.env['ir.model.fields'].browse(field)]
                else:
                    field = [0, 2, field]
                model_name = field[2].model
            elif write:
                if(type(field[1]) == int):
                    field = [
                        0, 2, self.env['ir.model.fields'].browse(field[1])]
                else:
                    field = [0, 2, field[2]]
                model_name = self.env['ir.model'].search(
                    [('id', '=', int(field[2]['model_id']))]).model
            else:
                model_name = self.env['ir.model'].search(
                    [('id', '=', field[2]['model_id'])]).model
            model_data = self.env['ir.model.data'].search(
                [('model', '=', model_name)], limit=1)
            external_id = "".join(
                [model_data.module, '.model_', (model_data.model.replace('.', '_'))])
            record = etree.Element("record")
            record.set("id", field[2]['field_description'].replace(
                ' ', '_').replace('.', ''))
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
            xml_field.set("name", 'depends')
            xml_field.text = str(field[2]['depends'])
            record.append(xml_field)
            xml_field = etree.Element("field")
            xml_field.set("name", 'compute')
            xml_field.text = str(field[2]['compute'])
            record.append(xml_field)
            root.append(record)
        return root

    def _generate_and_extend_cfdi(self, nodes):
        path_extend = etree.Element("data")
        path_extend.set("inherit_id", "l10n_mx_edi.cfdiv33")
        for node in nodes:
            if(type(node) == list):
                node = node[2]
            path = "".join(["//*[name()='cfdi:",
                            node['nodes'].split('/')[-1], "']"])
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
                attr.set("name", "".join(["t-att-", instance.name]))
                if(node['attribute_value']):
                    attr.text = "".join(["format_string('", node['attribute_value'],
                                         "') or ", instance.value])
                elif(all_fields and not inner_field):
                    if(all_fields.model == 'account.move.line'):
                        attr.text = "".join(["line.",
                                             self.get_field_name(all_fields),
                                             " or (", instance.value, ")"])
                    else:
                        attr.text = "".join(["record.",
                                             self.get_field_name(all_fields),
                                             " or (", instance.value, ")"])
                elif(inner_field and all_fields):
                    if(all_fields.model == 'account.move.line'):
                        attr.text = "".join(["line.", self.get_field_name(
                            all_fields), ".", self.get_field_name(inner_field), " or (", instance.value, ")"])
                    else:
                        attr.text = "".join(["record.", self.get_field_name(all_fields), ".", self.get_field_name(
                            inner_field), " or (", instance.value, ")"])
                xpath.append(attr)
                path_extend.append(xpath)
        path_extend = etree.tostring(
            path_extend, pretty_print=True, encoding='utf-8')
        return path_extend
