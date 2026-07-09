# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, timedelta,time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class WIPWorkOrderLine(models.Model):
    _name = "tw.work.order.wip.line"
    _description = "TW Work Order WIP Line"

    # 7: defaults methods

    # 8: fields
    tgl_wo = fields.Date('Tanggal Service')
    aging = fields.Integer('Aging WIP')
    plate_number = fields.Char('No Polisi')
    state_wo = fields.Char('State')
    status_wo = fields.Char('Status WO')
    type_wo = fields.Char('Type WO')
    is_validasi_adh = fields.Boolean('Verifikasi ADH')
    description = fields.Char('Keterangan')
    motorbike_physics = fields.Selection([('Ada','Ada'),('Tidak Ada','Tidak Ada')],string="Fisik Motor")
    validation_status = fields.Selection([('draft','Draft'),('open','Open'),('done','Done')],default='draft')

    # 9: relation fields
    wip_id = fields.Many2one('tw.work.order.wip','WIP Order')
    wo_id = fields.Many2one('tw.work.order','Work Order')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods