from email.policy import default
from odoo import fields, models, api, _
from lxml import etree


class AddendaConditional(models.Model):
    _name = 'addenda.conditional'
    _description = 'Add t-if t-else conditionals to a tag'

    value_condition = fields.Char(string='Value Condition')
    field_condition = fields.Many2one(string='Field Condition', comodel_name='ir.model.fields', domain=[(
        'model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field_condition = fields.Many2one(
        string='Inner Field Condition', comodel_name='ir.model.fields')
    inner_field_condition_domain = fields.Char(
        string='Inner Field Condition Domain')
    field_type_condition = fields.Char(compute='_compute_field_type_condition')
    condition = fields.Selection([('==', '=='), ('!=', '!='), ('>', '>'), (
        '<', '<'), ('>=', '>='), ('<=', '<=')], string='Condition', default='==')
    value_equal = fields.Char(string='Value Equal')
    field_equal = fields.Many2one(string='Field Equal', comodel_name='ir.model.fields', domain=[(
        'model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field_equal = fields.Many2one(
        string='Inner Field Equal', comodel_name='ir.model.fields')
    inner_field_equal_domain = fields.Char(string='Inner Field Equal Domain')
    field_type_equal = fields.Char(compute='_compute_field_type_equal')
    value = fields.Char(string='Value')
    field = fields.Many2one(string='Field', comodel_name='ir.model.fields', domain=[(
        'model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field = fields.Many2one(
        string='Inner Field', comodel_name='ir.model.fields')
    inner_field_domain = fields.Char(string='Inner Field Domain')
    field_type = fields.Char(compute='_compute_field_type')
    addenda_tag_id = fields.Many2one(
        string='Addenda Tag', comodel_name='addenda.tag')
    preview = fields.Text(string='Preview', compute='_compute_preview', help=(
        'A preview to help the user to create the xml'), store=True)

    @ api.depends('value_condition', 'field_condition', 'inner_field_condition', 'value_equal', 'field_equal', 'inner_field_equal', 'value', 'field', 'inner_field', 'condition', 'addenda_tag_id.tag_name')
    def _compute_preview(self):
        for condition in self:
            condition_value = ''
            equal_value = ''
            esc_value = ''
            if condition.addenda_tag_id.tag_name:
                tag_name = condition.addenda_tag_id.tag_name.replace(' ', '_')
            else:
                tag_name = 'TagName'

            if condition.value_condition:
                condition_value = "".join(
                    ["'", condition.value_condition, "'"])
            elif condition.field_condition and not condition.inner_field_condition:
                condition_value = "".join(
                    ["record.", condition.field_condition.name])
            elif condition.field_condition and condition.inner_field_condition:
                condition_value = "".join(
                    ["record.", condition.field_condition.name, ".", condition.inner_field_condition.name])

            if condition.value_equal:
                equal_value = "".join(
                    ["'", condition.value_equal, "'"])
            elif condition.field_equal and not condition.inner_field_equal:
                equal_value = "".join(
                    ["record.", condition.field_equal.name])
            elif condition.field_equal and condition.inner_field_equal:
                equal_value = "".join(
                    ["record.", condition.field_equal.name, ".", condition.inner_field_equal.name])

            if condition.value:
                esc_value = condition.value
            elif condition.field and not condition.inner_field:
                esc_value = "".join(
                    ["record.", condition.field.name])
            elif condition.field and condition.inner_field:
                esc_value = "".join(
                    ["record.", condition.field.name, ".", condition.inner_field.name])

            t = etree.Element('t')
            t.set('t-if', "".join([condition_value, " ",
                  condition.condition, " ", equal_value]))
            inside_tag = etree.Element(tag_name)
            inside_tag.text = esc_value
            t.append(inside_tag)
            condition.preview = etree.tostring(t, pretty_print=True)

    @ api.depends('field_condition')
    def _compute_field_type_condition(self):
        for condition in self:
            if condition.field_condition:
                condition.field_type_condition = condition.field_condition.ttype
            else:
                condition.field_type_condition = False

    @ api.depends('field_equal')
    def _compute_field_type_equal(self):
        for condition in self:
            if condition.field_equal:
                condition.field_type_equal = condition.field_equal.ttype
            else:
                condition.field_type_equal = False

    @ api.depends('field')
    def _compute_field_type(self):
        for condition in self:
            if condition.field:
                condition.field_type = condition.field.ttype
            else:
                condition.field_type = False

    @ api.onchange('field_condition')
    def _generate_inner_fields_condition_domain(self):
        for condition in self:
            if condition.field_condition:
                condition.inner_field_condition_domain = condition.field_condition.relation
            else:
                condition.inner_field_condition_domain = False

    @ api.onchange('field_equal')
    def _generate_inner_fields_equal_domain(self):
        for condition in self:
            if condition.field_equal:
                condition.inner_field_equal_domain = condition.field_equal.relation
            else:
                condition.inner_field_equal_domain = False

    @ api.onchange('field')
    def _generate_inner_fields_domain(self):
        for condition in self:
            if condition.field:
                condition.inner_field_domain = condition.field.relation
            else:
                condition.inner_field_domain = False

    @ api.onchange('field_condition', 'value_condition')
    def change_condition(self):
        for condition in self:
            if condition.value_condition not in ("", False):
                condition.field_condition = False
                condition.inner_field_condition = False
            elif condition.field_condition not in ("", False):
                condition.value_condition = False

    @ api.onchange('field_equal', 'value_equal')
    def change_equal(self):
        for condition in self:
            if condition.value_equal not in ("", False):
                condition.field_equal = False
                condition.inner_field_equal = False
            elif condition.field_equal not in ("", False):
                condition.value_equal = False

    @ api.onchange('field', 'value')
    def change_field(self):
        for condition in self:
            if condition.value not in ("", False):
                condition.field = False
                condition.inner_field = False
            elif condition.field not in ("", False):
                condition.value = False
