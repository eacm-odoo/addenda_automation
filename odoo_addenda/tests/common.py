from odoo.addons.l10n_mx_edi_40.tests.common import TestMxEdiCommon
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


# test everything from the module
@tagged('post_install_l10n_mx_edi', '-at_install', 'post_install')
class TestAddendaAutomation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("Prepare testing Data!-----------")

        # region Create Addenda from expression
        cls.addenda_field_test = cls.env['ir.model.fields'].create({
            'name': 'x_addendaTestField',
            'model_id': 409,
            'field_description': 'Addenda Expression Test Field',
            'ttype': 'text',
            'copied': True,
            'store': True,
        }
        )
        cls.addenda_from_expression = cls.env['addenda.addenda'].create({
            'name': 'Addenda_from_expression_Test',
            'is_expression': True,
            'is_customed_addenda': False,
            'addenda_expression': '<Addenda > <asdfasf > <asdfasdf > <xcvxcvxc > <vxcvxc/> </xcvxcvxc > </asdfasdf > </asdfasf ></Addenda >',
            'fields': [cls.addenda_field_test.id],
        })

        # endregion

        # region Create Addenda for barry

        # create tag for addenda
        cls.tag_initial = cls.env['addenda.tag'].create({
            'tag_name': 'Initial',
        })
        # create tag for addenda
        cls.tag_orden_compra = cls.env['addenda.tag'].create({
            'tag_name': 'OrdenCompra',
            'field': 3919,
            'addenda_tag_id': cls.tag_initial.id,
        })

        cls.tag_partner = cls.env['addenda.tag'].create({
            'tag_name': 'Partner',
            'field': 3936,
            'inner_field': 906,
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
            'field': 3919,
            'addenda_tag_id': cls.attribute_tag.id,
        })

        # create attribute with inner field
        cls.addenda_barry_field_test_3 = cls.env['addenda.attribute'].create({
            'attribute': 'addendaTestInnerField',
            'field': 3936,
            'inner_field': 906,
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

        print(cls.addenda_barry)
        # endregion

        # # region Create addenda inherit from CDFI Template
        # cls.addenda_inherit = cls.env['addenda.addenda'].create({
        #     'name': 'Addenda Inherit',
        #     'is_expression': False,
        #     'main_preview': False,
        #     'is_customed_addenda': True,
        #     'tag_name': 'Initial'})
        # # endregion
