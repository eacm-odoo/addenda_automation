from odoo import models, fields, api
import xml.etree.ElementTree as ET
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
        
        #recover the res.partner from account.move
        partner_id = list(res.keys())[0].partner_id
        if partner_id.is_customed_addenda:
            _logger.info('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
            nodes_ids = partner_id.addenda_addenda.nodes_ids#node that include, path, position and expression
            _logger.info(nodes_ids)
            datas = res[next(iter(res))]['attachment'].datas #datas field from ir.attachment, contains the binary of the cfdi xml
            xml = ET.fromstring(base64.decodebytes(datas))#transform from binary to string to xml
            _logger.info(xml)
            _logger.info('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')
        return res
