import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddendaAddenda(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name', required=True)
    nodes_ids = fields.One2many(comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
    is_customed_addenda = fields.Boolean(string='Customed Addenda')
    expression = fields.Text(string='Expression')

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
