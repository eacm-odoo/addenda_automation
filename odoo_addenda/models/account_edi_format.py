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
        _logger.info('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        _logger.info(res)
        datas = res[next(iter(res))]['attachment'].datas
        _logger.info(datas)
        xml_in_str = base64.decodebytes(datas)
        _logger.info(xml_in_str)
        _logger.info('__________________________________________________________________________________')
        xml = ET.fromstring(xml_in_str)
        _logger.info(xml)
        _logger.info('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')
        return res
