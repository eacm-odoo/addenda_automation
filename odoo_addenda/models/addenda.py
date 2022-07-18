import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AddendaAddenda(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name', required=True,help=_('The name of the new customed addenda'))
    nodes_ids = fields.One2many(comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
    is_customed_addenda = fields.Boolean(string='Customed Addenda', )
    expression = fields.Text(string='Expression')
    fields = fields.One2many(comodel_name='ir.model.fields',string="Fields",inverse_name='addenda_id')

    @api.onchange('expression')
    def evalue_expression(self):
        for node in self:
            if(node.expression):
                try:
                    ET.fromstring(node.expression)
                except:
                    raise UserError(_("invalid format for xml"))
                    
    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        self.generate_xml_fields(vals_list['fields'])
        if not(vals_list['is_customed_addenda']):
            
            ir_ui_view = self.env['ir.ui.view'].create({
                'name': vals_list['name'],
                'type': 'qweb',
                'arch': vals_list['expression'],
                'active': True,
                'inherit_id': False,
                'model': False,
                'priority': 16,
                'arch_base': vals_list['expression'],
                'arch_db': vals_list['expression'],
                'arch_fs': False,
                'mode': 'primary',
                'l10n_mx_edi_addenda_flag': True,
            })
        return res
    
    def generate_xml_fields(self,fields):
        root=ET.Element('data')
        for field in fields:
            model_name = self.env['ir.model'].search([('id','=',field[2]['model_id'])]).model
            record_node=self.generate_xml_element('record','',{'id':field[2]['field_description'],'model':model_name})
            record_node.append(self.generate_xml_element('field',field[2]['name'],{'name':'name'}))
            record_node.append(self.generate_xml_element('field',field[2]['field_description'],{'name':'field_description'}))
            record_node.append(self.generate_xml_element('field',field[2]['ttype'],{'name':'ttype'}))
            record_node.append(self.generate_xml_element('field',field[2]['model_id'],{'name':'model_id'}))
            root.append(record_node)
            
        _logger.info(ET.tostring(root, xml_declaration=True))


        return root


    def generate_xml_element(self,name,text,attrs):
        new_element = ET.Element(name,attrs)
        new_element.text=str(text)
        return new_element
