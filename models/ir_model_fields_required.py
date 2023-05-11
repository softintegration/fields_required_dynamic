# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IrModelFieldsRequired(models.Model):
    _name = 'ir.model.fields.required'
    _description = 'Required model fields'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(compute='_compute_model_name',store=True)
    fields_ids = fields.Many2many('ir.model.fields', 'ir_model_fields_required_fields', 'model_field_required_id', 'field_id',
                                  string='Fields to be required')
    domain = fields.Char(string="Application domain")
    active = fields.Boolean('Active', default=True)

    @api.depends('model_id')
    def _compute_model_name(self):
        for each in self:
            each.model_name = each.model_id.model

    @api.onchange('model_id')
    def onchange_model_id(self):
        self.fields_ids = False


    @api.constrains('model_id', 'fields_ids')
    def _check_model_fields_coherence(self):
        if self.model_id and self.fields_ids:
            model_ids = self.fields_ids.mapped('model_id')
            if any(model.id != self.model_id.id for model in model_ids):
                raise UserError(_("One or many fields selected does not belong to selected model!"))

    def _get_configured_required_fields(self,model_name):
        domain = [('model_name','=',model_name)]
        rule_model = self.search(domain)
        rule_fields = [field.name for field in rule_model.fields_ids]
        rule_domain = rule_model.domain
        return rule_fields,rule_domain

