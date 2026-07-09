# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
import odoo.addons.base.models.decimal_precision as dp

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritNrfsMFT(models.Model):
    _inherit = "tw.nrfs"
    # INFO : Override from NRFS and Connected to MFT
    
    # 7: defaults methods

    # 8: fields
    urgent_po_number = fields.Char(string='No PO Urgent MD', size=50)
    urgent_po_date = fields.Date(string='Tanggal PO Urgent')
    is_urgent_po = fields.Boolean(string='Dipenuhi dengan PO Urgent?')
    
    urgent_ppo_filename = fields.Char(string='Nama File PPO')
    urgent_ppo_send_date = fields.Date(string='Tanggal Kirim PPO')
    is_urgent_ppo_mft = fields.Boolean(string='Sudah kirim MFT PPO?', default=False)

    # 9: relation fields
    mft_nrfs_history_ids = fields.One2many('tw.nrfs.mft.history', 'nrfs_id', string='History MFT NRFS')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_confirm_md_sparepart(self):
        po_urg_line = []
        for line in self.line_ids:
            if line.is_urgent_po:
                po_urg_line.append(line.id)
        if po_urg_line:
            now_date = date.today()
            urgent_po_number = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('URG', self.company_id.code)
            self.line_ids.browse(po_urg_line).write({
                'urgent_po_number': urgent_po_number,
                'urgent_po_date': now_date.strftime('%Y-%m-%d')
            })
            self.write({
                'is_urgent_po': True,
                'urgent_po_number': urgent_po_number,
                'urgent_po_date': now_date.strftime('%Y-%m-%d')
            })
        else:
            self.write({'is_p2p_md': True})

    # 14: private methods
    
    