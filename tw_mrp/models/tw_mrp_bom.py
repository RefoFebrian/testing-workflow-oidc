# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, Command,fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessError
from odoo.osv.expression import AND, OR

# 5: local imports

# 6: Import of unknown third party lib

class InheritMrpBom(models.Model):
    _inherit = "mrp.bom"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_mrp.group_tw_mrp_bom_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    
    # 13: action methods
    def action_copy(self):
        self.ensure_one()
        return {
            'name': _('Copy Extras'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.mrp.copy.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_source_bom_id': self.id,
            }
        }

    # 14: private methods
    @api.model
    def _bom_find_domain(self, products, picking_type=None, company_id=False, bom_type=False):
        domain = ['&', '|', ('product_id', 'in', products.ids), '&', ('product_id', '=', False), ('product_tmpl_id', 'in', products.product_tmpl_id.ids), ('active', '=', True)]
        if company_id or self.env.context.get('company_id'):
            domain = AND([domain, ['|', ('company_id', '=', False), ('company_id', 'parent_of', company_id or self.env.context.get('company_id'))]])
        if picking_type:
            domain = AND([domain, ['|', ('picking_type_id', '=', picking_type.id), ('picking_type_id', '=', False)]])
        if bom_type:
            domain = AND([domain, [('type', '=', bom_type)]])
        return domain
    