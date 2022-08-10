from odoo.tests.common import TransactionCase
from odoo.tests import tagged


# test everything from the module
@tagged('post_install_l10n_mx_edi', '-at_install', 'post_install')
class TestAddendaAutomation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #print("Prepare testing Data!-----------")

        # region Create Field
        cls.addenda_field_test = cls.env['ir.model.fields'].create({
            'name': 'x_addendaTestField',
            'model_id': cls.env.ref('account.model_account_move').id,
            'field_description': 'Addenda Expression Test Field',
            'ttype': 'text',
            'copied': True,
            'store': True,
        }
        )
        # endregion

        # region Create Addenda for barry

        # create tag for addenda
        cls.tag_initial = cls.env['addenda.tag'].create({
            'tag_name': 'Initial',
        })

        # search for fields
        account_move_name = cls.env['ir.model.fields'].search(
            [('model', '=', 'account.move'), ('name', '=', 'name')]).id
        account_move_partner_id = cls.env['ir.model.fields'].search(
            [('model', '=', 'account.move'), ('name', '=', 'partner_id')]).id
        account_move_partner_id_name = cls.env['ir.model.fields'].search(
            [('model', '=', 'res.partner'), ('name', '=', 'name')]).id

        # create tag for addenda
        cls.tag_orden_compra = cls.env['addenda.tag'].create({
            'tag_name': 'OrdenCompra',
            'field': account_move_name,
            'addenda_tag_id': cls.tag_initial.id,
        })

        cls.tag_partner = cls.env['addenda.tag'].create({
            'tag_name': 'Partner',
            'field': account_move_partner_id,
            'inner_field': account_move_partner_id_name,
            'addenda_tag_id': cls.tag_initial.id,
        })

        cls.attribute_tag = cls.env['addenda.tag'].create({
            'tag_name': 'Attribute',
            'addenda_tag_id': cls.tag_partner.id,
        })
        # create atribute with value
        cls.addenda_barry_field_test = cls.env['addenda.attribute'].create({
            'attribute': 'addendaTestValue',
            'value': 'testValue',
            'addenda_tag_id': cls.attribute_tag.id,
        })
        # create atribute with field
        cls.addenda_barry_field_test_2 = cls.env['addenda.attribute'].create({
            'attribute': 'addendaTestField',
            'field': account_move_name,
            'addenda_tag_id': cls.attribute_tag.id,
        })

        # create attribute with inner field
        cls.addenda_barry_field_test_3 = cls.env['addenda.attribute'].create({
            'attribute': 'addendaTestInnerField',
            'field': account_move_partner_id,
            'inner_field': account_move_partner_id_name,
            'addenda_tag_id': cls.attribute_tag.id,
        })
        # update tag_initial with tag_orden_compra

        cls.addenda_barry = cls.env['addenda.addenda'].create({
            'name': 'Addenda for Barry',
            'is_expression': False,
            'main_preview': False,
            'is_customed_addenda': False,
            'tag_name': 'Initial',
            'fields': [],
            'addenda_tag_id': [(6, 0, cls.tag_initial.id)]
        })
        cls.attribute_tag.attribute_ids = [cls.addenda_barry_field_test.id,
                                           cls.addenda_barry_field_test_2.id, cls.addenda_barry_field_test_3.id]
        cls.tag_initial.addenda_addenda_id = cls.addenda_barry.id
        # update tag_initial with tag_orden_compra
        cls.tag_initial.addenda_tag_childs_ids = [
            cls.tag_orden_compra.id, cls.tag_partner.id, cls.attribute_tag.id]

        # endregion

        # region Create addenda with tree tag and a created field
        cls.tree_tag_with_created_field = cls.env['addenda.tag'].create({
            'tag_name': 'TreeTagWithCreatedField',
        })

        cls.tag_created_field = cls.env['addenda.tag'].create({
            'tag_name': 'CreatedField',
            'field':  cls.addenda_field_test.id,
            'addenda_tag_id': cls.tree_tag_with_created_field.id,
        })
        cls.tree_tag_with_created_field.addenda_tag_childs_ids = [
            cls.tag_created_field.id]

        cls.addenda_field = cls.env['addenda.addenda'].create({
            'name': 'Addenda for Barry',
            'is_expression': False,
            'main_preview': False,
            'is_customed_addenda': False,
            'tag_name': 'Initial',
            'fields': [],
            'addenda_tag_id': [(6, 0, cls.tree_tag_with_created_field.id)]
        })
        # end region

        # region Create addenda inherit from CDFI Template

        cls.addenda_inherit = cls.env['addenda.addenda'].create({
            'name': 'Addenda Inherit',
            'is_expression': False,
            'main_preview': False,
            'is_customed_addenda': True,
            'fields': [],
            'nodes_ids': [],
            'tag_name': 'Root'})

        cls.addenda_node_1 = cls.env['addenda.node'].create({
            'nodes': 'Comprobante/Emisor',
            'position': 'after',
            'addenda_id': cls.addenda_inherit.id,
            'addenda_tag_ids': [(6, 0, cls.tag_initial.id)],
        })
        cls.addenda_node_2 = cls.env['addenda.node'].create({
            'nodes': 'Comprobante/Receptor',
            'position': 'before',
            'addenda_id': cls.addenda_inherit.id,
            'addenda_tag_ids': [(6, 0, cls.tag_orden_compra.id)],
        })

        cls.addenda_node_3 = cls.env['addenda.node'].create({
            'nodes': 'Comprobante/Conceptos/Concepto/Impuestos/Retenciones/Retencion',
            'position': 'attributes',
            'addenda_id': cls.addenda_inherit.id,
            'addenda_tag_ids': [(6, 0, cls.tag_partner.id)],
            'cfdi_attributes': 33,
            'attribute_value': 'Exento',
        })

        cls.addenda_node_4 = cls.env['addenda.node'].create({
            'nodes': 'Comprobante/Impuestos/Retenciones/Retencion',
            'position': 'attributes',
            'addenda_id': cls.addenda_inherit.id,
            'addenda_tag_ids': [(6, 0, cls.tag_partner.id)],
            'cfdi_attributes': 32,
            'attribute_value': 'Exento',
        })
        cls.addenda_inherit.nodes_ids = [
            cls.addenda_node_1.id, cls.addenda_node_2.id, cls.addenda_node_3.id, cls.addenda_node_4.id]

        # endregion
