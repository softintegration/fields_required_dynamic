# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import ast
from odoo.osv.expression import DOMAIN_OPERATORS

NESTED_OBJECT_FIELD_SIGN = "."


class IrModelFieldsRequired(models.Model):
    _name = 'ir.model.fields.required'
    _description = 'Required model fields'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(compute='_compute_model_name', store=True)
    fields_ids = fields.Many2many('ir.model.fields', 'ir_model_fields_required_fields', 'model_field_required_id',
                                  'field_id',
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

    def _get_configured_required_fields(self, model_name):
        domain = [('model_name', '=', model_name)]
        rule_model = self.search(domain)
        rule_fields = [field.name for field in rule_model.fields_ids]
        rule_domain = rule_model.domain
        return rule_fields, rule_domain

    @api.model
    def _parse_domain(self, model, domain):
        """ This method will parse the domain specified by the user so that it will be accepted by the user interface modifiers
        in Odoo,the interface doesn't accept the nested object in domain filter,so this type of filters must be parsed before that thy be applyed
        to the interface"""
        domain = ast.literal_eval(domain)
        new_domain = []
        for domain_token in domain:
            # in the case the domain is not nested we have to continue
            if domain_token in DOMAIN_OPERATORS:
                new_domain.append(domain_token)
                continue
            if not self._nested_object_field(domain_token):
                new_domain.append(domain_token)
                continue
            # in the case of nested field we have to reform the domain so that the "modifiers" of the view will accept it
            domain_token = self._reform_domain_token(model,domain_token)
            new_domain.append(domain_token)
        return new_domain

    @api.model
    def _reform_domain_token(self,model,domain_token):
        leaf_field = self._get_field_in_domain_token(domain_token)
        new_domain_token = [leaf_field.split(NESTED_OBJECT_FIELD_SIGN)[0],'in']
        nested_field = leaf_field.split(NESTED_OBJECT_FIELD_SIGN)
        field_name = nested_field.pop(0)
        field = self.env[model]._fields[field_name]
        model = field.comodel_name
        field_name = NESTED_OBJECT_FIELD_SIGN.join(nested_field)
        built_domain = [(field_name,domain_token[1],domain_token[2])]
        nested_object_ids = self.env[model].search(built_domain).ids
        new_domain_token.insert(2,nested_object_ids)
        return new_domain_token

    @api.model
    def _nested_object_field(self, domain_token):
        return NESTED_OBJECT_FIELD_SIGN in self._get_field_in_domain_token(domain_token)

    @api.model
    def _get_field_in_domain_token(self, domain_token):
        return domain_token[0]
