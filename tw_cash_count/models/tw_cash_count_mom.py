# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwCashCountBeritaAcaraWizard(models.TransientModel):
    _name = "tw.cash.count.berita.acara.wizard"
    _description = "Cash Count Berita Acara Wizard"


    # 7: defaults methods

    # 8: fields
    note = fields.Text('Note')
    options = fields.Selection([('ALL','ALL'),('POS','POS'),('Showroom','Showroom')])

    # 9: relation fields
    cash_count_id = fields.Many2one('tw.cash.count','Cash Count')

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods
    @api.onchange('cash_count_id','options')
    def onchange_note(self):
        if self.cash_count_id and self.options:
            if self.options == 'POS':
                self.note = self.cash_count_id.note_ba_pos
            elif self.options == 'Showroom':
                self.note = self.cash_count_id.note_ba_sr
            else:
                self.note = self.cash_count_id.note_ba

    # 12: Override Methods

    # 13: Action Methods
    def action_submit(self):
        active_ids = self.env.context.get('active_ids', [])
        user = self.env['res.users'].browse(self._uid).name

        # Cash
        saldo_fisik_cash = 0
        cash_detail = []

        # Petty Cash SR
        plafon_petty_cash_sr = self.cash_count_id.plafon_petty_cash_sr
        saldo_sistem_petty_cash_sr = 0
        saldo_physical_petty_cash_sr = self.cash_count_id.physical_petty_cash_sr
        balance_pc_sr = self.cash_count_id.balance_pc_sr
        saldo_sistem_reimburse_sr = 0
        petty_cash_sr_detail = []
        reimburse_petty_cash_sr_detail = []

        # Petty Cash WS
        plafon_petty_cash_ws = self.cash_count_id.plafon_petty_cash_ws
        saldo_sistem_petty_cash_ws = 0
        saldo_physical_petty_cash_ws = self.cash_count_id.physical_petty_cash_ws
        balance_pc_ws = self.cash_count_id.balance_pc_ws
        saldo_sistem_reimburse_ws = 0
        petty_cash_ws_detail = []
        reimburse_petty_cash_ws_detail = []
    
        # Petty Cash ATL/BTL
        plafon_petty_cash_atl_btl = self.cash_count_id.plafon_petty_cash_atl_btl
        saldo_sistem_petty_cash_atl_btl = 0
        saldo_physical_petty_cash_atl_btl = self.cash_count_id.physical_petty_cash_atl_btl
        balance_pc_atl_btl = self.cash_count_id.balance_pc_atl_btl
        saldo_sistem_reimburse_atl_btl = 0
        petty_cash_atl_btl_detail = []
        reimburse_petty_cash_atl_btl_detail = []
        
        # Penerimaan Lain
        saldo_fisik_other = 0
        other_detail = []

        for x in self.cash_count_id.cash_detail_ids:
            if self.options == 'POS':
                if 'POS' in x.journal:
                    if x.validation_id.name == 'Belum disetor ke bank':
                        cash_detail.append({
                            'name':x.name,
                            'journal':x.journal,
                            'amount':x.amount,
                            'amount_fisik':x.physical_amount,
                            'selisih':x.selisih,
                        })
                        saldo_fisik_cash += x.amount

            elif self.options == 'Showroom':
                if 'POS' in x.journal:
                    continue
                if x.validation_id.name == 'Belum disetor ke bank':
                    cash_detail.append({
                        'name':x.name,
                        'journal':x.journal,
                        'amount':x.amount,
                        'amount_fisik':x.physical_amount,
                        'selisih':x.selisih,
                    })
                    saldo_fisik_cash += x.amount

            else:
                if x.validation_id.name == 'Belum disetor ke bank':
                    cash_detail.append({
                        'name':x.name,
                        'journal':x.journal,
                        'amount':x.amount,
                        'amount_fisik':x.physical_amount,
                        'selisih':x.selisih,
                    })
                    saldo_fisik_cash += x.amount

        # TODO: mapping journal untuk cash count
        for x in self.cash_count_id.petty_cash_detail_ids:
            petty_cash_sr_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'description':x.description,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,
                    'validasi':x.validation_id.name,
                    'keterangan':x.note,
                })
            saldo_sistem_petty_cash_sr += x.amount  
            if 'SR' in x.journal:
                petty_cash_sr_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'description':x.description,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,
                    'validasi':x.validation_id.name,
                    'keterangan':x.note,
                })
                saldo_sistem_petty_cash_sr += x.amount

            elif 'WS' in x.journal:
                petty_cash_ws_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'description':x.description,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,
                    'validasi':x.validation_id.name,
                    'keterangan':x.note,
                })
                saldo_sistem_petty_cash_ws += x.amount
            
            elif 'ATLBTL' in x.journal:
                petty_cash_atl_btl_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'description':x.description,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,
                    'validasi':x.validation_id.name,
                    'keterangan':x.note,
                })
                saldo_sistem_petty_cash_atl_btl += x.amount

        for x in self.cash_count_id.reimburse_petty_cash_detail_ids:
            reimburse_petty_cash_sr_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,    
                })
            saldo_sistem_reimburse_sr += x.amount 
            if 'SR' in x.journal:
                reimburse_petty_cash_sr_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,    
                })
                saldo_sistem_reimburse_sr += x.amount 

            elif 'WS' in x.journal:
                reimburse_petty_cash_ws_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,    
                })
                saldo_sistem_reimburse_ws += x.amount
            
            elif 'ATLBTL' in x.journal:
                reimburse_petty_cash_atl_btl_detail.append({
                    'name':x.name,
                    'journal':x.journal,
                    'date': x.date.strftime('%d-%m-%Y') if x.date else '',
                    'amount':x.amount,    
                })
                saldo_sistem_reimburse_atl_btl += x.amount


        for x in self.cash_count_id.other_receivable_ids:
            other_detail.append({
                'name':x.name,
                'amount':x.amount,
                'keterangan':x.note,    
            })
            saldo_fisik_other += x.amount
            

        if self.options == 'POS':
            self.cash_count_id.note_ba_pos = self.note
            
        elif self.options == 'Showroom':
            self.cash_count_id.note_ba_sr = self.note
        else:
            self.cash_count_id.note_ba = self.note


        # * Get SOH and ADH Approval
        soh_id = ''
        adh_id = ''
        soh_on = ''
        adh_on = ''
        if getattr(self.cash_count_id,'approval_ids', False):
            for data in self.cash_count_id.approval_ids:
                if data.approval_id.group_id.name in ('SALES OPERATION HEAD','BRANCH HEAD'):
                    # Use sudo() to bypass multi-company access restriction on hr.employee
                    employee = data.approval_id.user_id.sudo().employee_id
                    soh_id = employee.name if employee else ''
                    soh_on = data.approval_id.approved_on
            
                if data.approval_id.group_id.name in ('ADMINISTRATION HEAD'):
                    # Use sudo() to bypass multi-company access restriction on hr.employee
                    employee = data.approval_id.user_id.sudo().employee_id
                    adh_id = employee.name if employee else ''
                    adh_on = data.approval_id.approved_on
            

        total_saldo_sistem_petty_cash_sr = (plafon_petty_cash_sr - balance_pc_sr - saldo_sistem_petty_cash_sr - saldo_sistem_reimburse_sr)
        total_saldo_sistem_petty_cash_ws = (plafon_petty_cash_ws - balance_pc_ws - saldo_sistem_petty_cash_ws - saldo_sistem_reimburse_ws)
        total_saldo_sistem_petty_cash_atl_btl = (plafon_petty_cash_atl_btl - balance_pc_atl_btl - saldo_sistem_petty_cash_atl_btl - saldo_sistem_reimburse_atl_btl)
        total_saldo_fisik = saldo_fisik_cash + saldo_physical_petty_cash_sr + saldo_physical_petty_cash_ws + saldo_physical_petty_cash_atl_btl + saldo_fisik_other
        
        selisih_petty_cash_sr = total_saldo_sistem_petty_cash_sr - saldo_physical_petty_cash_sr
        selisih_petty_cash_ws = total_saldo_sistem_petty_cash_ws - saldo_physical_petty_cash_ws
        selisih_petty_cash_atl_btl = total_saldo_sistem_petty_cash_atl_btl - saldo_physical_petty_cash_atl_btl

        datas = {
            'name':self.cash_count_id.name,
            'branch':self.cash_count_id.company_id.name,
            'lokasi':'Pos & Showroom',
            'tanggal': self.cash_count_id.date.strftime('%d-%m-%Y') if self.cash_count_id.date else '',
            'saldo_fisik_cash':saldo_fisik_cash,
            'cash_detail':cash_detail,
            'plafon_petty_cash_sr':plafon_petty_cash_sr,
            'saldo_sistem_petty_cash_sr':saldo_sistem_petty_cash_sr,
            'saldo_physical_petty_cash_sr':saldo_physical_petty_cash_sr,
            'balance_pc_sr':balance_pc_sr,
            'selisih_petty_cash_sr':selisih_petty_cash_sr,
            'saldo_sistem_reimburse_sr':saldo_sistem_reimburse_sr,
            'petty_cash_sr_detail':petty_cash_sr_detail,
            'reimburse_petty_cash_sr_detail':reimburse_petty_cash_sr_detail,
            'plafon_petty_cash_ws':plafon_petty_cash_ws,
            'saldo_sistem_petty_cash_ws':saldo_sistem_petty_cash_ws,
            'saldo_physical_petty_cash_ws':saldo_physical_petty_cash_ws,
            'balance_pc_ws':balance_pc_ws,
            'selisih_petty_cash_ws':selisih_petty_cash_ws,
            'saldo_sistem_reimburse_ws':saldo_sistem_reimburse_ws,
            'petty_cash_ws_detail':petty_cash_ws_detail,
            'reimburse_petty_cash_ws_detail':reimburse_petty_cash_ws_detail,
            'plafon_petty_cash_atl_btl':plafon_petty_cash_atl_btl,
            'saldo_sistem_petty_cash_atl_btl':saldo_sistem_petty_cash_atl_btl,
            'saldo_physical_petty_cash_atl_btl':saldo_physical_petty_cash_atl_btl,
            'balance_pc_atl_btl':balance_pc_atl_btl,
            'selisih_petty_cash_atl_btl':selisih_petty_cash_atl_btl,
            'saldo_sistem_reimburse_atl_btl':saldo_sistem_reimburse_atl_btl,
            'petty_cash_atl_btl_detail':petty_cash_atl_btl_detail,
            'reimburse_petty_cash_atl_btl_detail':reimburse_petty_cash_atl_btl_detail,
            'note':self.note,
            'options':self.options,
            'kasir':self.cash_count_id.cashier_id.name,
            'admin_pos':self.cash_count_id.admin_pos_id.name,
            'adh':self.cash_count_id.adh_id.name,
            'soh':self.cash_count_id.soh_id.name,
            'total_saldo_sistem_petty_cash_sr':total_saldo_sistem_petty_cash_sr,
            'total_saldo_sistem_petty_cash_ws':total_saldo_sistem_petty_cash_ws,
            'total_saldo_sistem_petty_cash_atl_btl':total_saldo_sistem_petty_cash_atl_btl,
            'total_saldo_fisik':total_saldo_fisik,
            'saldo_fisik_other':saldo_fisik_other,
            'other_detail':other_detail,
            'total_saldo_sistem_all':saldo_fisik_cash+total_saldo_sistem_petty_cash_sr+total_saldo_sistem_petty_cash_ws+total_saldo_sistem_petty_cash_atl_btl,
            'create_uid':self.cash_count_id.create_uid.name,
            'approved_adh_uid':adh_id,
            'approved_soh_uid':soh_id,
            'create_date':self.cash_count_id.create_date,
            'approved_adh_on':adh_on,
            'approved_soh_on':soh_on,

        }
        datas = {
            "ids": active_ids,
            "model": "tw.cash.count",
            "form": datas,
            "user": user
        }
    
        return self.env.ref('tw_cash_count.action_print_bakso_cash_count').report_action(self, data=datas)

    # 14: Private Methods
 
    