import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddendaNode(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name')
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
            new_addenda = ('''
            <odoo>
                    <template id="l10_mx_edi_''' + vals_list['name'].lower().replace(" ", "") + '" name="' +  vals_list['name'].lower().replace(" ", "") + '"><Addenda>\n ')
            new_addenda += vals_list['expression'] + '\n'
            new_addenda += '''
                                </Addenda>
                </template>
            </odoo>
                    '''
            ir_ui_view = self.env['ir.ui.view'].create({
                'name': vals_list['name'],
                'type': 'qweb',
                'arch': new_addenda,
                'active': True,
                'inherit_id': False,
                'model': False,
                'priority': 16,
                'arch_base': new_addenda,
                'arch_db': new_addenda,
                'arch_fs': False,
                'mode': 'primary',
                'l10n_mx_edi_addenda_flag': True,
            })
        return res
