from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class PartHotline(models.Model):
    _name = "tw.part.hotline"
    _inherit = ["tw.part.hotline", "tw.approval.mixin"]

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(selection_add=[
        ('waiting_for_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('done',),
    ], ondelete={'waiting_for_approval': 'set null', 'approved': 'set null'})

    # 11: compute/depends & on change methods

    # 12: override methods
        
    def action_rfa(self):
        self._check_minimal_dp()
        self._check_available_part()
        if not self.part_detail_ids:
            raise Warning('Part detail tidak boleh kosong !')
        
        if self.state != 'draft':
            for dp in self.alocation_dp_ids:
                if dp.amount_hl_allocation > dp.hl_id.amount_residual_currency:
                    raise Warning('Nilai Alokasi tidak boleh lebih besar dari Amount Balance ! Number %s \n Nilai Amount Residual RP. %s ' %(dp.hl_id.ref,dp.hl_id.amount_residual_currency))
                
                oustanding_alokasi = self.env['tw.part.hotline.alocation.dp'].search([
                    ('hotline_id','!=',self.id),
                    ('hl_id','=',dp.hl_id.id),
                    ('hotline_id.state','in',('waiting_for_approval','approved'))
                ],limit=1)
                if oustanding_alokasi:
                    raise Warning('Silahkan cek kembali alokasi %s. Alokasi sudah digunakan pada transaksi %s' % (oustanding_alokasi.hl_id.ref, oustanding_alokasi.hotline_id.name))
            
        max_qty = 1
        warning_status_dp = False
        warning_available = False

        if self.amount_dp < self.minimal_dp:
            warning_status_dp = True
        for x in self.part_detail_ids:
            if x.state == 'draft':
                return True
            if x.is_available:
                warning_available = True
            if x.qty > max_qty:
                max_qty = x.qty

        # Status Value 0 Open , 2 SPV Part , 1 SSA 
        total_value = 0
        if self.is_exception:
            if int(max_qty) > 1 or warning_available:
                total_value = 2
            
            if warning_status_dp:
                total_value = 1
        else:
            message = ''
            no = 1
            if warning_available:
                message += '%s. Product %s tersedia di cabang sekitar ! \n'%(no,x.product_id.display_name)
                no += 1
            if warning_status_dp:
                message += '%s. DP minimal harus setengah dari Amount Total ! \n'%(no)
                no += 1
            if int(max_qty) > 1:
                message += '%s. Max qty hanya boleh 1 per product ! \n'%(no)
                no += 1
            if message:
                message += 'Gunakan exceptions jika dibutuhkan'
                raise Warning('Perhatian ! \n %s'%(message))
        return super().action_request_approval(value=total_value)

    def action_approval(self):
        self._check_available_part()
        return super().action_approval()

    def action_reject_or_cancel(self):
        return super().action_reject_or_cancel()

    def _check_minimal_dp(self):
        if self.minimal_dp <= 0:
            raise Warning('Minimal DP tidak boleh 0.\nHarap Setting Minimal DP Part Hotline pada menu Branch Setting untuk Cabang %s' % self.company_id.name)
        minimal_dp = self.minimal_dp
        allocation_dp = self.amount_dp
        if allocation_dp < minimal_dp:
            raise Warning('Amount DP lebih kecil dari Minimal DP !')