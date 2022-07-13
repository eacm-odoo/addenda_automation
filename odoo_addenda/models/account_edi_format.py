from odoo import models, fields, api
from lxml import etree
import base64
import logging

_logger = logging.getLogger(__name__)


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    # override method _post_invoice_edi to add addenda

    def _post_invoice_edi(self, invoices):
        res = super()._post_invoice_edi(invoices)
        if self.code != 'cfdi_3_3':
            return res

        # recover the res.partner from account.move
        partner_id = list(res.keys())[0].partner_id
        if not partner_id.addenda_addenda and not partner_id.l10n_mx_edi_addenda:
            return res
        if partner_id.is_customed_addenda:
            _logger.info(
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
            # node that include, path, position and expression
            nodes_ids = partner_id.addenda_addenda.nodes_ids
            _logger.info(res)
            # datas field from ir.attachment, contains the binary of the cfdi xml
            datas = res[next(iter(res))]['attachment'].datas
            # transform from binary to string to xml
            xml = etree.fromstring(base64.decodebytes(datas))
            xml = self.add_nodes(xml, nodes_ids, next(iter(res)))
            res[next(iter(res))]['attachment'].datas = base64.encodebytes(
                etree.tostring(xml))

            new_xml = base64.encodebytes(etree.tostring(
                xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
            self.env['ir.attachment'].search(
                [('id', '=', res[next(iter(res))]['attachment'].id)]).write({'datas': new_xml, 'mimetype': 'application/xml'})
            _logger.info(
                'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')
        return res

    # inside the parent, create a new tag with text
    def add_new_tag_inside(self, parent, element):
        parent.append(element)
        return element

    # add new tag after a given node
    def add_new_tag_after(self, parent, element, parent_map):
        position = list(parent_map[parent]).index(parent)
        parent_map[parent].insert(position+1, element)

    # add new tag before a given node
    def add_new_tag_before(self, parent, element, parent_map):
        position = list(parent_map[parent]).index(parent)
        parent_map[parent].insert(position, element)

    # add attribute to an existing tag
    def add_attribute_to_tag(self, parent, attribute, value):
        parent.set(attribute, value)

    # create method to add node to the xml

    def add_nodes(self, xml, nodes_ids,account_move):
        parent_map = {c: p for p in xml.iter()
                      for c in p}
        for node in nodes_ids:
            parent = xml.find(node.path)
            if node.position == 'attributes':
                self.add_attribute_to_tag(
                    parent, node.attribute, node.attribute_value)
            else:
                root_node = etree.Element(etree.QName(
                'http://www.sat.gob.mx/cfd/3', node.tag_name))
                # call generate_node ->tag tree
                for tag in node.addenda_tag_id:
                    child_node = self.generate_node(tag, account_move)
                    root_node.append(child_node)
                if node.position == 'after':
                    self.add_new_tag_after(
                        parent, root_node, parent_map)
                elif node.position == 'before':
                    self.add_new_tag_before(
                        parent, root_node, parent_map)
                elif node.position == 'inside':
                    self.add_new_tag_inside(parent, root_node)
        return xml

    def generate_node(self, addenda_tag, account_move):
        parent_node = etree.Element(addenda_tag.tag_name)
        if addenda_tag.addenda_tag_childs_ids:
            for child in addenda_tag.addenda_tag_childs_ids:
                child_node = self.generate_node(child, account_move)
                parent_node.append(child_node)
        if addenda_tag.field and not addenda_tag.attribute:
            field_name = addenda_tag.field.name
            _logger.info(account_move)
            _logger.info(field_name)
            _logger.info(addenda_tag.field.ttype)
            text = self.env['account.move'].search(
                [('id', '=', account_move.id)])[field_name]
            _logger.info(text)
            parent_node.text = text
        elif addenda_tag.attribute and addenda_tag.value:
            parent_node.set(addenda_tag.attribute,addenda_tag.value)
        elif addenda_tag.attribute and addenda_tag.field:
            field_name = addenda_tag.field.name
            text = self.env['account.move'].search(
                [('id', '=', account_move.id)])[field_name]
            parent_node.set(addenda_tag.attribute,text)
        elif not addenda_tag.attribute and not addenda_tag.field and addenda_tag.value:
            parent_node.text = addenda_tag.value

        return parent_node
