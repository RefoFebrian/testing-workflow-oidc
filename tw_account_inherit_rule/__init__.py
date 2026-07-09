# -*- coding: utf-8 -*-

from . import models

def post_init_hook_function(env):
    coa_rule = env.ref('account.account_comp_rule', raise_if_not_found=False)
    if coa_rule:
        coa_rule.domain_force = "[('company_ids', 'parent_of', company_ids)]"
    
    journal_rule = env.ref('account.journal_comp_rule', raise_if_not_found=False)
    if journal_rule:
        journal_rule.domain_force = "[('company_id', 'parent_of', company_ids)]"
    
    move_line_rule = env.ref('account.account_move_line_comp_rule', raise_if_not_found=False)
    if move_line_rule:
        move_line_rule.domain_force = "[('company_id', 'in', company_ids)]"
    
    tax_rule = env.ref('account.tax_comp_rule', raise_if_not_found=False)
    if tax_rule:
        tax_rule.domain_force = "['|',('company_id', 'parent_of', company_ids),('company_id','=',False)]"
    
    partner_bank_rule = env.ref('base.res_partner_bank_rule', raise_if_not_found=False)
    if partner_bank_rule:
        partner_bank_rule.domain_force = "['|',('company_id', 'parent_of', company_ids),('company_id','=',False)]"