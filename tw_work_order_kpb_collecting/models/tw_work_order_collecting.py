# -*- coding: utf-8 -*-

# 1: imports of python lib
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderCollecting(models.Model):
    _inherit = "tw.work.order.collecting"

    # 7: defaults methods

    # No additional fields needed — claim_type_id on parent already covers KPB
    # via tw.selection records with type='WorkOrderClaimType' and value='KPB'

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    def _prepare_onchange_branch_type_date(self):
        """Override: tambah logika due_date untuk KPB (90 hari)."""
        result = super()._prepare_onchange_branch_type_date()

        # Due Date untuk KPB: 90 hari dari hari ini
        today = self._get_default_date()
        if self.claim_type_id and self.claim_type_id.value == 'KPB':
            self.due_date = today + relativedelta(days=90)
            return self.due_date

        return result

    @api.onchange('company_id', 'claim_type_id', 'start_date', 'end_date')
    def _onchange_branch_type_date(self):
        self.work_order_ids = False
        self.collecting_line_ids = False
        self.due_date = False
        self.amount = 0.0
        if self.claim_type_id:
            self._prepare_onchange_branch_type_date()
        
    @api.onchange('company_id')
    def branch_change(self):
        self.supplier_id=self.company_id.default_supplier_id

    # 12: override methods    
    def action_get_detail(self):
        wo = []
        self.transaction_message = False
        limit = 50
        if not self.claim_type_id:
            raise ValidationError(_('Pilih Claim Type terlebih dahulu.'))
        work_order_obj = self.env['tw.work.order'].search([
            ('company_id', '=', self.company_id.id),
            ('collecting_work_order_id', '=', False),
            ('state', '=', 'sale'),
            ('claim_state', '=', 'draft'),
            ('claim_type_id', '=', self.claim_type_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])

        # Filter: hanya ambil WO yang invoice receivable line-nya belum ter-reconcile
        work_order_obj = self._filter_wo_unreconciled(work_order_obj)

        if work_order_obj:
            length = len(work_order_obj)
            if length > limit:
                del work_order_obj[limit:]
                transaction_remaining = length // limit or 1
                self.transaction_message = 'Anda menggenerate "%s WO dari total %s WO yang harus di proses" di transaksi ini. \nSilahkan buat setidaknya %s collecting lagi untuk menyelesaikannya. ' % (limit, length, transaction_remaining)
            for work_order in work_order_obj:
                wo.append(work_order.id)
            self.write({'work_order_ids': [(6, 0, wo)]})
            self.get_rekap_collecting_line_ids()
        else:
            raise ValidationError(_('Data Tidak Ditemukan'))
        
    def _prepare_query_rekap_collecting_line_ids(self, wo_ids, claim_journal_ids):
        """Override: gunakan query KPB (group by kpb_ke) jika claim type adalah KPB."""
        if self.claim_type_id and self.claim_type_id.value == 'KPB':
            wo_tuple = str(tuple(wo_ids)).replace(',)', ')')
            journal_tuple = str(tuple(claim_journal_ids)).replace(',)', ')')

            query = f"""
                SELECT 
                    wo_count.kpb_ke,
                    wo_count.qty,
                    COALESCE(inv_sum.total_jasa, 0) AS total_jasa,
                    COALESCE(inv_sum.total_oli, 0) AS total_oli
                FROM (
                    SELECT 
                        wo.kpb_ke AS kpb_ke,
                        COUNT(wo.id) AS qty,
                        wo.company_id
                    FROM tw_work_order wo
                    WHERE wo.id IN {wo_tuple}
                    GROUP BY wo.kpb_ke, wo.company_id
                ) AS wo_count
                FULL OUTER JOIN (
                    SELECT 
                        wo.kpb_ke,
                        wo.company_id,
                        COALESCE(SUM(aml.price_total) FILTER (WHERE pp.division = 'Service'), 0) AS total_jasa,
                        COALESCE(SUM(aml.price_total) FILTER (WHERE pp.division = 'Sparepart'), 0) AS total_oli
                    FROM tw_work_order wo
                    INNER JOIN account_move am ON wo.name = am.invoice_origin
                        AND am.move_type = 'out_invoice'
                        AND am.state = 'posted'
                        AND am.journal_id IN {journal_tuple}
                    INNER JOIN account_move_line aml ON aml.move_id = am.id
                        AND aml.display_type = 'product'
                        AND aml.price_total > 0
                    INNER JOIN product_product pp ON pp.id = aml.product_id
                    WHERE wo.id IN {wo_tuple}
                    GROUP BY wo.kpb_ke, wo.company_id
                ) AS inv_sum ON wo_count.company_id = inv_sum.company_id AND wo_count.kpb_ke = inv_sum.kpb_ke
                WHERE 1=1
            """
            return query
        return super()._prepare_query_rekap_collecting_line_ids(wo_ids, claim_journal_ids)
            
    def _prepare_journal_account(self, account_setting_obj=None):
        """
        Override: ambil journal KPB dari master tw.work.order.claim.
        Konsisten dengan base class yang sudah menggunakan _get_claim_master().
        Untuk KPB, journal_id di master claim langsung digunakan.
        Untuk claim type lain, delegate ke super().
        """
        if self.claim_type_id and self.claim_type_id.value == 'KPB':
            # Gunakan _get_claim_master() yang sudah ada di base class
            claim_master = self._get_claim_master()
            if not claim_master.journal_id:
                raise ValidationError(_('Journal pada master Claim Type "KPB" belum di-setting.'))
            if not claim_master.journal_id.default_debit_account_id:
                raise ValidationError(
                    _('Default Debit Account pada journal "%s" (Claim Type KPB) belum di-setting.')
                    % claim_master.journal_id.name
                )
            return claim_master.journal_id.id, claim_master.journal_id.default_debit_account_id.id
        return super()._prepare_journal_account(account_setting_obj)