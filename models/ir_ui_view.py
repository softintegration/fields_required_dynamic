# -*- coding: utf-8 -*-


from lxml import etree
from odoo import models, SUPERUSER_ID, api
from odoo.addons.base.models.ir_ui_view import transfer_field_to_modifiers
import logging
import ast

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _postprocess_tag_field(self, node, name_manager, node_info):
        super(IrUiView, self)._postprocess_tag_field(node, name_manager, node_info)
        required_fields,required_domain = self.env['ir.model.fields.required']._get_configured_required_fields(name_manager.model._name)
        if not required_fields or not required_domain:
            return
        if node.tag == 'field' and node.get('name'):
            field = name_manager.model._fields.get(node.get('name'))
            if field.name in required_fields:
                node_info['modifiers'].update({'required':ast.literal_eval(required_domain)})
