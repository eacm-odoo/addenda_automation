from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    addenda_addenda = fields.Many2one(
        comodel_name="addenda.addenda", string="Addenda Customed created by User", domain = [('is_customed_addenda', '=', True)])
    is_customed_addenda = fields.Boolean(string="Is Customed Addenda")
    
    @api.depends('is_customed_addenda')
    def _compute_addenda(self):
        for record in self:
            if self.is_customed_addenda:
                self.l10n_mx_edi_addenda = None
            else:
                self.addenda_addenda = None
            
    @api.onchange('is_customed_addenda')
    def onchange_is_customed_addenda(self):
        if self.is_customed_addenda:
            self.l10n_mx_edi_addenda = False
        else:
            self.addenda_addenda = False