# -*- coding: utf-8 -*-

from . import models

def post_init_hook_function(env):
    job_rule = env.ref('hr.hr_job_comp_rule', raise_if_not_found=False)
    if job_rule:
        job_rule.domain_force = "[ '|', ('company_id', 'parent_of', company_ids), ('company_id', '=', False)]"
    
    dept_rule = env.ref('hr.hr_dept_comp_rule', raise_if_not_found=False)
    if dept_rule:
        dept_rule.domain_force = "[ '|', ('company_id', 'parent_of', company_ids), ('company_id', '=', False)]"
    