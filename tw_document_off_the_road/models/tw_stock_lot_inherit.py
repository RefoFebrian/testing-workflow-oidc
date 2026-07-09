# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class StockLotInherit(models.Model):
    _inherit = "stock.lot"

    # 7: defaults methods

    # 8: fields
    vehicle_document_submission_date = fields.Date('Tgl Penyerahan Faktur')
    process_otr_date = fields.Date('Tgl Pengurusan STNK & BPKB')

    # 9: relation fields
    vehicle_document_submission_id = fields.Many2one('tw.submission.off.the.road',string="No Penyerahan Faktur")
    process_otr_id = fields.Many2one('tw.process.off.the.road',string="Pengurusan STNK & BPKB")
    inv_process_otr_id = fields.Many2one('account.move','Invoice Pengurusan STNK & BPKB',domain=[('move_type','=','in_invoice')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods