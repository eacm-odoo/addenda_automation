from odoo import models, fields, api


class AddendaAddenda(models.Model):
    _name = 'addenda.addenda'
    _description = 'Automated addenda'

    name = fields.Char(string='Name')
    nodes_ids = fields.One2many(
        comodel_name='addenda.node', string='Nodes', inverse_name='addenda_id')
    
    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        ir_ui_view = self.env['ir.ui.view'].create({
            'name': vals['name'],
            'type': 'qweb',
            'arch': '<Company>\n <Employee>\n <FirstName>Tanmay</FirstName>\n </Employee>\n </Company>\n <template id="addenda_test" inherit_id="l10n_mx_edi.cfdiv33">\n <xpath expr="/cfdi:Emisor" position="after">\n<test>Hola<test>\n</xpath>\n </template>',
            'active': True,
            'inherit_id': False,
            'model': False,
            'priority': 16,
            'arch_base': '<?xml version="1.0"?>\n<Company>\n <Employee>\n <FirstName>Tanmay</FirstName>\n </Employee>\n </Company>\n <template id="addenda_test" inherit_id="l10n_mx_edi.cfdiv33">\n <xpath expr="/cfdi:Emisor" position="after">\n<test>Hola<test>\n</xpath>\n </template>',
            'arch_db': '<Company>\n <Employee>\n <FirstName>Tanmay</FirstName>\n </Employee>\n </Company>\n <template id="addenda_test" inherit_id="l10n_mx_edi.cfdiv33">\n <xpath expr="/cfdi:Emisor" position="after">\n<test>Hola<test>\n</xpath>\n </template>',
            'arch_fs': False,
            'mode': 'primary',
            'l10n_mx_edi_addenda_flag': True,
        })
        return res