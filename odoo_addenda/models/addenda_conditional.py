from odoo import fields, models, api, _


class AddendaConditional(models.Model):
    _name = 'addenda.conditional'
    _description = 'Add t-if t-else conditionals to a tag'

    value_condition = fields.Char(string='Value Condition')
    field_condition = fields.Many2one(string='Field Condition', comodel_name='ir.model.fields', domain=[('model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field_condition = fields.Many2one(string='Inner Field Condition', comodel_name='ir.model.fields')
    inner_field_condition_domain = fields.Char(string='Inner Field Condition Domain')
    field_type_condition = fields.Char(compute='_compute_field_type_condition')
    condition = fields.Selection([('==', '=='), ('!=', '!='), ('>', '>'), ('<', '<'), ('>=', '>='), ('<=', '<=')], string='Condition')
    value_equal = fields.Char(string='Value Equal')
    field_equal = fields.Many2one(string='Field Equal', comodel_name='ir.model.fields', domain=[('model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field_equal = fields.Many2one(string='Inner Field Equal', comodel_name='ir.model.fields')
    inner_field_equal_domain = fields.Char(string='Inner Field Equal Domain')
    field_type_equal = fields.Char(compute='_compute_field_type_equal')
    value = fields.Char(string='Value')
    field = fields.Many2one(string='Field', comodel_name='ir.model.fields', domain=[('model', '=', 'account.move'), ('ttype', 'not in', ('binary', 'html', 'many2one_reference'))])
    inner_field = fields.Many2one(string='Inner Field', comodel_name='ir.model.fields')
    inner_field_domain = fields.Char(string='Inner Field Domain')
    field_type = fields.Char(compute='_compute_field_type')
    addenda_tag_id = fields.Many2one(string='Addenda Tag', comodel_name='addenda.tag')
    preview = fields.Text(string='Preview', compute='_compute_preview', help=('A preview to hel the user to create the xml'))

    # @api.depends('value_condition', 'field_condition', 'inner_field_condition', 'condition', 'value_equal', 'field_equal', 'inner_field_equal', 'value', 'field', 'inner_field')
    # def _compute_preview(self):
    #     for condition in self:
    #         preview = ''
    #         if condition.value_condition:
    #             preview += '<t-if t-value="{} {} {}">'.format(condition.value_condition, condition.condition, condition.value_equal)
    #         if condition.field_condition:
    #             preview += '<t-if t-field="{} {} {}">'.format(condition.field_condition, condition.condition, condition.field_equal)
    #         if condition.inner_field_condition:
    #             preview += '<t-if t-field="{} {} {}">'.format(condition.inner_field_condition, condition.condition, condition.inner_field_equal)
    #         if condition.value:
    #             preview += '<t-if t-value="{} {} {}">'.format(condition.value, condition.condition, condition.value_equal)
    #         if condition.field:
    #             preview += '<t-if t-field="{} {} {}">'.format(condition.field, condition.condition, condition.field_equal)
    #         if condition.inner_field:
    #             preview += '<t-if t-field="{} {} {}">'.format(condition.inner_field, condition.condition, condition.inner_field_equal)
    #         if condition.value_condition or condition.field_condition or condition.inner_field_condition:
    #             preview += '</t-if>'
    #         condition.preview = preview
    
    @api.depends('field_condition')
    def _compute_field_type_condition(self):
        for condition in self:
            if condition.field_condition:
                condition.field_type_condition = condition.field_condition.ttype
            else:
                condition.field_type_condition = False

    @api.depends('field_equal')
    def _compute_field_type_equal(self):
        for condition in self:
            if condition.field_equal:
                condition.field_type_equal = condition.field_equal.ttype
            else:
                condition.field_type_equal = False
    
    @api.depends('field')
    def _compute_field_type(self):
        for condition in self:
            if condition.field:
                condition.field_type = condition.field.ttype
            else:
                condition.field_type = False

    @api.onchange('field_condition')
    def _generate_inner_fields_condition_domain(self):
        for condition in self:
            if condition.field_condition:
                condition.inner_field_condition_domain = condition.field_condition.relation
            else:
                condition.inner_field_condition_domain = False
    
    @api.onchange('field_equal')
    def _generate_inner_fields_equal_domain(self):
        for condition in self:
            if condition.field_equal:
                condition.inner_field_equal_domain = condition.field_equal.relation
            else:
                condition.inner_field_equal_domain = False
    
    @api.onchange('field')
    def _generate_inner_fields_domain(self):
        for condition in self:
            if condition.field:
                condition.inner_field_domain = condition.field.relation
            else:
                condition.inner_field_domain = False
