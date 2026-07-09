# -*- coding: utf-8 -*-

def _tw_pricelist_post_init(env):
    env['res.config.settings'].create({
        'group_product_pricelist': True,  # Activate pricelist
    }).execute()

    if env.ref('tw_pricelist.is_only_use_pricelist', False):
        env.ref('tw_pricelist.is_only_use_pricelist').write({'active': True}).execute()


from . import models
