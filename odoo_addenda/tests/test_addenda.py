from .common import TestAddendaAutomation
from odoo.tests import tagged


@tagged('post_install_l10n_mx_edi', 'post_install', '-at_install')
class TestAddendaAutomationResults(TestAddendaAutomation):

    def test_super_simple(self):
        print("Result of Testing!!")
        print(self.addenda_barry.main_preview)
        print("----------------------------------------------------")
        self.assertEqual(self.addenda_barry.main_preview,
                         '<Initial>\n    <Initial>\n        <OrdenCompra>\n            <t t-esc="record.name"/>\n        </OrdenCompra>\n        <Partner>\n            <t t-esc="record.partner_id.name"/>\n        </Partner>\n        <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n    </Initial>\n</Initial>\n')
