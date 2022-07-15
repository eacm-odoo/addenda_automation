from lxml.objectify import fromstring
import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AddendaTag(models.Model):
    _name = 'addenda.tag'
    _description = 'Add tag to node in addenda'

    addenda_node_id = fields.Many2one(
        string='Addenda Node', comodel_name='addenda.node')
    addenda_addenda_id = fields.Many2one(
        string='Addenda Addenda', comodel_name='addenda.addenda')
    addenda_tag_childs_ids = fields.One2many(
        comodel_name='addenda.tag', string='Addenda Tag Childs', inverse_name='addenda_tag_id', help=_('New elements added inside this tag/element'))
    addenda_tag_id = fields.Many2one(
        string='Addenda tag', comodel_name='addenda.tag')
    tag_name = fields.Char(string='Tag Name', required=True,
                           help=_('Name of the new tag/element'))
    attribute = fields.Char(string='Attribute', help=_(
        'Name of the attribute of the new element'))
    value = fields.Char(string='Attribute Value', help=_(
        'Value of the attribute of the new element'))
    field = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields',
        domain=[('model', '=', 'account.move'), ('ttype', 'in', ('char', 'text', 'selection', 'many2one', 'monetary', 'integer', 'boolean', 'date', 'datetime'))])
    inner_field = fields.Many2one(
        string='Inner field', help=_(''), comodel_name='ir.model.fields')
    preview = fields.Text(store=False, string='Preview',
                          readonly=True, compute='_compute_preview')

    @api.onchange('field')
    def _compute_inner_fields(self):
        domain = {'inner_field': []}
        for record in self:
            if record.field.ttype == 'many2one':
                domain = {'inner_field': [
                    ('model', '=', record.field.relation), ('ttype', 'not in', ('many2one'))]}
        return {'domain': domain}

    @api.onchange('addenda_tag_childs_ids')
    def _remove_field(self):
        for record in self:
            if len(record.addenda_tag_childs_ids) > 0:
                record.field = False

    @api.onchange('field')
    def _remove_child_tags(self):
        for record in self:
            if record.field:
                record.addenda_tag_childs_ids = False

    @api.onchange('value')
    def _remove_field(self):
        for record in self:
            if record.value:
                record.field = False

    @api.depends('tag_name', 'attribute', 'value', 'field', 'addenda_tag_childs_ids')
    def _compute_preview(self):
        tag = self.tag_name or 'Tag name'
        attr = self.attribute or ''
        value = (self.field.name or self.value) or 'Value'
        childs = ""
        if self.addenda_tag_childs_ids:
            for child_tag in self.addenda_tag_childs_ids:
                childs = childs + '\n\t<' + child_tag.tag_name + '>'
            childs = childs + '\n'
        #childs= '\n\t<child> </child>\n\t.\n\t.\n\t.\n' if len(self.addenda_tag_childs_ids) >0 else ''

        self.preview = ("<cfdi:%s %s> %s </cfdi:%s>" % (tag, ('%s=%s' %
                        (attr, value)) if attr != '' else '', childs, tag))
