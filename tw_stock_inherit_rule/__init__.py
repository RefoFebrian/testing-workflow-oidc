# -*- coding: utf-8 -*-

from . import models

def post_init_hook_function(env):
    stock_location_rule = env.ref('stock.stock_location_comp_rule', raise_if_not_found=False)
    if stock_location_rule:
        stock_location_rule.domain_force = "[('company_id', 'in', company_ids + [False])]"
    