# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class TwPartnerBranch(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:        
            if vals.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().browse(vals['company_id'])
                doc_code = branch_src.code
                vals['id_customer'] = self.env['ir.sequence'].suspend_security().get_sequence_code('CUS', doc_code)
        
        create = super(TwPartnerBranch, self).create(vals_list)
        return create

    def write(self,vals):
       
        return super(TwPartnerBranch, self).write(vals)


    # 13: action methods
    # TODO: Area_id belum ada pada res_users

    def action_res_partner_customer_tree(self):
        action_customer_tree = super(TwPartnerBranch,self).action_res_partner_customer_tree()
        areas = self.env['res.users'].suspend_security().browse(self._uid).area_id.company_ids
        action_customer_tree['domain']= [('company_id', 'in', [b.id for b in areas])]
        return action_customer_tree
      
    
    def action_res_partner_supplier_tree(self):
        action_supplier_tree = super(TwPartnerBranch,self).action_res_partner_supplier_tree()
        areas = self.env['res.users'].suspend_security().browse(self._uid).area_id.company_ids
        action_supplier_tree['domain'] = [('is_vendor','=',True),('company_id', 'in', [b.id for b in areas])]
        return action_supplier_tree 

    # 14: private methods


