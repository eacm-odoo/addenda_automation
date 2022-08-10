from lxml import etree

from .common import TestAddendaAutomation
from odoo.tests import tagged


@tagged('post_install_l10n_mx_edi', 'post_install', '-at_install')
class TestAddendaAutomationResults(TestAddendaAutomation):

    def test_computed_fields(self):
        # print("Result of Testing!!")
        # print(
        #     self.addenda_barry.addenda_tag_id[0].addenda_tag_childs_ids[2].attribute_ids[1].field_type)
        # print("-----------------------FINISHHHHHHHHHHHHHHHHH---------------------------")
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
        #print("RESULT OF TESTING METHODS")
        generate_tree_view = self.addenda_barry.generate_tree_view(
            self.addenda_barry.addenda_tag_id[0])
        self.assertEqual(etree.tostring(generate_tree_view, pretty_print=True),
                         b'<Initial>\n  <OrdenCompra>\n    <t t-esc="record.name"/>\n  </OrdenCompra>\n  <Partner>\n    <t t-esc="record.partner_id.name"/>\n  </Partner>\n  <Attribute addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')

        field_name = self.addenda_barry.get_field_name(
            self.addenda_barry.addenda_tag_id[0].addenda_tag_childs_ids[0].field.id)
        self.assertEqual(field_name, 'name')

        field_ttype = self.addenda_barry.get_field_type(
            self.addenda_barry.addenda_tag_id[0].addenda_tag_childs_ids[0].field.id)
        self.assertEqual(field_ttype, 'char')

        root = etree.Element(self.addenda_barry.tag_name.replace(' ', '_'))
        root.append(generate_tree_view)
        get_xml = self.addenda_barry.get_xml(self.addenda_barry.name, root)
        #print(etree.tostring(get_xml, pretty_print=True))

    def test_addenda_expression(self):
        addenda_from_expression = self.env['addenda.addenda'].create({
            'name': 'Addenda_from_expression_Test',
            'is_expression': True,
            'is_customed_addenda': False,
            'addenda_expression': '''<Initial>
                                        <Initial>
                                            <OrdenCompra>
                                                <t t-esc="record.name"/>
                                            </OrdenCompra>
                                            <Partner>
                                                <t t-esc="record.partner_id.name"/>
                                            </Partner>
                                            <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>
                                        </Initial>
                                    </Initial>''',
            'fields': [],
        })
        self.assertTrue(addenda_from_expression)

    def test_addenda_expression_with_new_fields(self):
        addenda_from_expression_with_new_fields = self.env['addenda.addenda'].create({
            'name': 'Addenda_from_expression_Test',
            'is_expression': True,
            'is_customed_addenda': False,
            'addenda_expression': '''<Initial>
                                        <Initial>
                                            <OrdenCompra>
                                                <t t-esc="record.x_addendaTestField"/>
                                            </OrdenCompra>
                                            <Partner>
                                                <t t-esc="record.partner_id.name"/>
                                            </Partner>
                                            <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.x_addendaTestField" t-att-addendaTestInnerField="record.partner_id.name"/>
                                        </Initial>
                                    </Initial>''',
            'fields': [self.addenda_field_test.id],
        })
        self.assertTrue(addenda_from_expression_with_new_fields)
        self.assertEqual(addenda_from_expression_with_new_fields.addenda_fields_xml,
                         '<odoo>\n  <record id="Addenda_Expression_Test_Field" model="ir.model.fields">\n    <field name="name">x_addendaTestField</field>\n    <field name="field_description">Addenda Expression Test Field</field>\n    <field name="model_id" ref="account.model_account_move"/>\n    <field name="ttype">text</field>\n    <field name="required">False</field>\n    <field name="readonly">False</field>\n    <field name="store">True</field>\n    <field name="index">False</field>\n    <field name="copied">True</field>\n  </record>\n</odoo>\n')
        self.assertNotEqual(
            addenda_from_expression_with_new_fields.addenda_fields_xml, '<odoo/>\n')

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

        # Computed fields for addenda
        self.assertEqual(addenda.main_preview,
                         '<Initial>\n    <Initial>\n        <OrdenCompra>\n            <t t-esc="record.name"/>\n        </OrdenCompra>\n        <Partner>\n            <t t-esc="record.partner_id.name"/>\n        </Partner>\n        <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n    </Initial>\n</Initial>\n')
        self.assertNotEqual(addenda.main_preview,
                            '<Initial>\n    <Initial>\n        <OrdenCompra>\n            <t t-esc="record.number"/>\n        </OrdenCompra>\n        <Partner>\n            <t t-esc="record.parner.name"/>\n        </Partner>\n        <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n    </Initial>\n</Initial>\n')
        
        self.assertEqual(addenda.addenda_tag_id[0].preview,
                         '<Initial>\n    <OrdenCompra>\n        <t t-esc="record.name"/>\n    </OrdenCompra>\n    <Partner>\n        <t t-esc="record.partner_id.name"/>\n    </Partner>\n    <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')
        self.assertNotEqual(addenda.addenda_tag_id[0].preview,
                            '<Initial>\n    <OrdenCompra>\n        <t t-esc="record.number"/>\n    </OrdenCompra>\n    <Partner>\n        <t t-esc="record.parner.name"/>\n    </Partner>\n    <Attribute t-att-addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')

        self.assertEqual(
            addenda.addenda_tag_id[0].addenda_tag_childs_ids[0].field_type, 'char')
        self.assertNotEqual(
            addenda.addenda_tag_id[0].addenda_tag_childs_ids[0].field_type, 'integer')

        self.assertEqual(str(addenda.addenda_tag_id[0].len_tag_childs), '3')
        self.assertNotEqual(str(addenda.addenda_tag_id[0].len_tag_childs), '2')

        self.assertEqual(
            addenda.addenda_tag_id[0].addenda_tag_childs_ids[2].attribute_ids[1].field_type, 'char')
        self.assertNotEqual(
            addenda.addenda_tag_id[0].addenda_tag_childs_ids[2].attribute_ids[1].field_type, 'string')

        #test method from the addenda model
        generate_tree_view = addenda.generate_tree_view(
            addenda.addenda_tag_id[0])
        self.assertEqual(etree.tostring(generate_tree_view, pretty_print=True),
                         b'<Initial>\n  <OrdenCompra>\n    <t t-esc="record.name"/>\n  </OrdenCompra>\n  <Partner>\n    <t t-esc="record.partner_id.name"/>\n  </Partner>\n  <Attribute addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')
        self.assertNotEqual(etree.tostring(generate_tree_view, pretty_print=True),
                            b'<Initial>\n  <OrdenCompra>\n    <t t-esc="record.number"/>\n  </OrdenCompra>\n  <Partner>\n    <t t-esc="record.parner.name"/>\n  </Partner>\n  <Attribute addendaTestValue="testValue" t-att-addendaTestField="record.name" t-att-addendaTestInnerField="record.partner_id.name"/>\n</Initial>\n')

    def test_create_addenda_with_tree_tag_and_field(self):
        addenda = self.env['addenda.addenda'].create({
            'name': 'Addenda for Barry',
            'is_expression': False,
            'main_preview': False,
            'is_customed_addenda': False,
            'tag_name': 'Initial',
            'fields': [self.addenda_field_test.id],
            'addenda_tag_id': [(6, 0, self.tree_tag_with_created_field.id)]
        })

        self.assertTrue(addenda)
        generate_tree_view = addenda.generate_tree_view(
            addenda.addenda_tag_id[0])
        self.assertEqual(etree.tostring(generate_tree_view, pretty_print=True),
                        b'<TreeTagWithCreatedField>\n  <CreatedField>\n    <t t-esc="record.x_addendaTestField"/>\n  </CreatedField>\n</TreeTagWithCreatedField>\n')
        self.assertNotEqual(etree.tostring(generate_tree_view, pretty_print=True),
                            b'<t t-esc="record.x_addendaTestField"/>\n')    
        self.assertEqual(addenda.addenda_fields_xml, '<odoo>\n  <record id="Addenda_Expression_Test_Field" model="ir.model.fields">\n    <field name="name">x_addendaTestField</field>\n    <field name="field_description">Addenda Expression Test Field</field>\n    <field name="model_id" ref="account.model_account_move"/>\n    <field name="ttype">text</field>\n    <field name="required">False</field>\n    <field name="readonly">False</field>\n    <field name="store">True</field>\n    <field name="index">False</field>\n    <field name="copied">True</field>\n  </record>\n</odoo>\n')
        self.assertNotEqual(addenda.addenda_fields_xml, '<field name="x_addendaTestField"/>')
