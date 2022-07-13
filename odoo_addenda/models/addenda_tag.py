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
    tag_name = fields.Char(string='Tag Name')
    attribute = fields.Char(string='Attribute')
    value = fields.Char(string='Value')
