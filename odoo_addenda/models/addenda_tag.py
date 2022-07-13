from lxml.objectify import fromstring
import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddendaTag(models.Model):
    _name = 'addenda.tag'
    _description = 'Add tag to node in addenda'

    addenda_node_id = fields.Many2one(
        string='Addenda Node', comodel_name='addenda.node')
    addenda_tag_childs_ids = fields.One2many(
        comodel_name='addenda.tag', string='Addenda Tag Childs', inverse_name='addenda_tag_id')
    addenda_tag_id = fields.Many2one(
        string='Addenda tag', comodel_name='addenda.tag')
    tag_name = fields.Char(string='Tag Name', required=True)
    attribute = fields.Char(string='Attribute')
    value = fields.Char(string='Value')
    field = fields.Many2one(
        string='Field', help=_('The value that will appear on the invoice once generated'), comodel_name='ir.model.fields', 
        domain=[('model', '=', 'account.move'),('ttype', 'in',('char','text','selection'))])
    
    @api.onchange('addenda_tag_childs_ids')
    def _remove_field(self):
        for record in self:
            if len(record.addenda_tag_childs_ids)>0:
                record.field = False
                
    @api.onchange('field')
    def _remove_child_tags(self):
        for record in self:
            if record.field:
                record.addenda_tag_childs_ids=False
    
    @api.onchange('value')
    def _remove_field(self):
        for record in self:
            if record.value:
                record.field=False

                
            