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
            _logger.info(res[next(iter(res))]['attachment'].checksum)
            # datas field from ir.attachment, contains the binary of the cfdi xml
            datas = res[next(iter(res))]['attachment'].datas
            # transform from binary to string to xml
            xml = etree.fromstring(base64.decodebytes(datas))
            _logger.info(etree.tostring(xml))
            xml = self.add_nodes(xml, nodes_ids)
            res[next(iter(res))]['attachment'].datas = base64.encodebytes(
                etree.tostring(xml))
            
            new_xml = base64.encodebytes(etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
            self.env['ir.attachment'].search(
                [('id', '=', res[next(iter(res))]['attachment'].id)]).write({'datas': new_xml, 'mimetype': 'application/xml'})
            _logger.info(
                'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')
        return res


    # inside the parent, create a new tag with text
    def add_new_tag_inside(self,parent, element, tag_name):
        node = etree.Element(etree.QName('http://www.sat.gob.mx/cfd/3', tag_name))
        element = etree.fromstring(element)
        node.append(element)
        parent.append(node)
        return element

    # add new tag after a given node
    def add_new_tag_after(self,parent, element, parent_map, tag_name):
        node = etree.Element(etree.QName('http://www.sat.gob.mx/cfd/3', tag_name))
        element = etree.fromstring(element)
        node.append(element)
        position = list(parent_map[parent]).index(parent)
        parent_map[parent].insert(position+1, node)

    # add new tag before a given node
    def add_new_tag_before(self,parent, element, parent_map, tag_name):
        node = etree.Element(etree.QName('http://www.sat.gob.mx/cfd/3', tag_name))
        element = etree.fromstring(element)
        node.append(element)
        position = list(parent_map[parent]).index(parent)
        parent_map[parent].insert(position, node)
        
    #add attribute to an existing tag
    def add_attribute_to_tag(self, parent, attribute, value):
        parent.set(attribute,value)


    # create method to add node to the xml
    def add_nodes(self, xml, nodes_ids):
        parent_map = {c: p for p in xml.iter()
                      for c in p}
        for node in nodes_ids:
            parent = xml.find(node.path)
            if node.position == 'after':
                self.add_new_tag_after(parent, node.expression, parent_map, node.tag_name)
            elif node.position == 'before':
                self.add_new_tag_before(parent, node.expression, parent_map, node.tag_name)
            elif node.position == 'inside':
                self.add_new_tag_inside(parent, node.expression, node.tag_name)
            elif node.position == 'attributes':
                self.add_attribute_to_tag(parent, node.attribute, node.attribute_value)
        _logger.info(etree.tostring(xml))
        return xml

