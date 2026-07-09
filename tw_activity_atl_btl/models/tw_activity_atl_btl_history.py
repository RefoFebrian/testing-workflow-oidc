# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWActivityHistoryLocation(models.Model):
    _name = "tw.activity.detail.loc.history"
    _description = "History Location Activity"

    month = fields.Char('Bulan')
    qty = fields.Integer('Qty')
    
    # 9: relation fields
    activity_line_id = fields.Many2one('tw.activity.atl.btl.line','Activity Line', ondelete='cascade')
    history_detail_ids = fields.One2many('tw.history.loc.detail','history_id','Detail')


class TWHistoryLocationDetail(models.Model):
    _name = "tw.history.loc.detail"
    _description = "Detail History Location Activity"

    history_id = fields.Many2one('tw.activity.detail.loc.history','History',ondelete='cascade')
    product_id = fields.Many2one('product.product','Product')
    categ_id = fields.Many2one('product.category','Category',related='product_id.categ_id', store=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
