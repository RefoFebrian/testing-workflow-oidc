# -*- coding: utf-8 -*-

from . import models

def post_init_hook_function(env):
    coa_rule = env.ref('mrp.mrp_bom_line_rule', raise_if_not_found=False)
    if coa_rule:
        coa_rule.domain_force = "[('company_id', 'parent_of', company_ids)]"
    
    journal_rule = env.ref('mrp.mrp_bom_rule', raise_if_not_found=False)
    if journal_rule:
        journal_rule.domain_force = "[('company_id', 'parent_of', company_ids)]"