from .common import TestAddendaAutomation
from odoo.tests import tagged

from lxml import etree


@tagged('post_install_l10n_mx_edi', 'post_install', '-at_install')
class TestAddendaAutomationResults(TestAddendaAutomation):

    def test_computed_fields(self):
        print("Result of Testing!!")
        print(
            self.addenda_barry.addenda_tag_id[0].addenda_tag_childs_ids[2].attribute_ids[1].field_type)
        print("-----------------------FINISHHHHHHHHHHHHHHHHH---------------------------")
        self.assertEqual(self.addenda_barry.main_preview,
                         '<Initial>\n    <Initial>\n        <OrdenCompra>\n            <t t-esc="record.name"/>\n        </OrdenCompra>\n        <Partner>\n            <t t-esc="record.partner_id.name"/>\n        </Partner>\n        <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n    </Initial>\n</Initial>\n')
        self.assertEqual(self.addenda_barry.addenda_tag_id[0].preview,
                         '<Initial>\n    <OrdenCompra>\n        <t t-esc="record.name"/>\n    </OrdenCompra>\n    <Partner>\n        <t t-esc="record.partner_id.name"/>\n    </Partner>\n    <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')
        self.assertEqual(
            self.addenda_barry.addenda_tag_id[0].addenda_tag_childs_ids[0].field_type, 'char')
        self.assertEqual(
            str(self.addenda_barry.addenda_tag_id[0].len_tag_childs), '3')
        self.assertEqual(
            self.addenda_barry.addenda_tag_id[0].addenda_tag_childs_ids[2].attribute_ids[1].field_type, 'char')

    def test_methods_addenda_addenda(self):

        print("RESULT OF TESTING METHODS")
        generate_tree_view = self.addenda_barry.generate_tree_view(
            self.addenda_barry.addenda_tag_id[0])
        self.assertEqual(etree.tostring(generate_tree_view, pretty_print=True),
                         b'<Initial>\n  <OrdenCompra>\n    <t t-esc="record.name"/>\n  </OrdenCompra>\n  <Partner>\n    <t t-esc="record.partner_id.name"/>\n  </Partner>\n  <Attribute addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')

        print(generate_tree_view)

    def test_create_addenda_with_tree_tag(self):
        addenda = self.env['addenda.addenda'].create({
            'name': 'Addenda for Barry',
            'is_expression': False,
            'main_preview': False,
            'is_customed_addenda': False,
            'tag_name': 'Initial',
            'fields': [],
            'addenda_tag_id': [(6, 0, self.tag_initial.id)]
        })
        self.assertTrue(addenda)

        #Computed fields for addenda
        self.assertEqual(addenda.main_preview, 
                         '<Initial>\n    <Initial>\n        <OrdenCompra>\n            <t t-esc="record.name"/>\n        </OrdenCompra>\n        <Partner>\n            <t t-esc="record.partner_id.name"/>\n        </Partner>\n        <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n    </Initial>\n</Initial>\n')

        self.assertEqual(addenda.addenda_tag_id[0].preview,
                            '<Initial>\n    <OrdenCompra>\n        <t t-esc="record.name"/>\n    </OrdenCompra>\n    <Partner>\n        <t t-esc="record.partner_id.name"/>\n    </Partner>\n    <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')
        
        self.assertEqual(addenda.addenda_tag_id[0].addenda_tag_childs_ids[0].field_type, 'char')

        self.assertEqual(str(addenda.addenda_tag_id[0].len_tag_childs), '3')

        self.assertEqual(addenda.addenda_tag_id[0].addenda_tag_childs_ids[2].attribute_ids[1].field_type, 'char')

    def test_create_addenda_with_tree_tag_and_field(self):
        addenda = self.env['addenda.addenda'].create({
            'name': 'Addenda for Barry',
            'is_expression': False,
            'main_preview': False,
            'is_customed_addenda': False,
            'tag_name': 'Initial',
            'fields': [],
            'addenda_tag_id': [(6, 0, self.tree_tag_with_created_field.id)]
        })

        self.assertTrue(addenda)


