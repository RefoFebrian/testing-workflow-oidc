# -*- coding: utf-8 -*-
# TODO: pada saat install module pertama kali, field name & model_id di ir.default tidak ada sehingga menimbulkan error
# def _tw_stock_account_init(env):
#     env['ir.default'].search([('name','=','property_cost_method'),('model_id.model','=','product.category')]).unlink()

from . import models
