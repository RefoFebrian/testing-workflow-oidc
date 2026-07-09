# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwCashCount(models.Model):
    _name = "tw.cash.count"
    _description = "Cash Count"
    _order = "date DESC"

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()


    # 8: fields
    name = fields.Char('Name',compute='_compute_name',store=True)
    date = fields.Date('Tanggal',default=_get_default_datetime)
    generate_date = fields.Datetime('Generate on')
    type_cash_count = fields.Selection([('Showroom','Showroom'),('POS','POS')],default='Showroom')
    state = fields.Selection([
        ('draft','Draft'),
        ('posted','Posted'),
        ('cancelled','Cancelled')],default="draft")
    plafon_petty_cash_sr = fields.Float('Plafon Petty Cash SR')
    plafon_petty_cash_ws = fields.Float('Plafon Petty Cash WS')
    plafon_petty_cash_atl_btl = fields.Float('Plafon Petty Cash ATL/BTL')
    physical_petty_cash_sr = fields.Float('Fisik Petty Cash SR')
    physical_petty_cash_ws = fields.Float('Fisik Petty Cash WS')
    physical_petty_cash_atl_btl = fields.Float('Fisik Petty Cash ATL/BTL')
    balance_pc_sr = fields.Float('Saldo PC SR di Bank Out')
    balance_pc_ws = fields.Float('Saldo PC WS di Bank Out')
    balance_pc_atl_btl = fields.Float('Saldo PC ATL/BTL di Bank Out')
    note_ba = fields.Text('Note Berita Acara')
    note_ba_sr = fields.Text('Note Berita Acara SR')
    note_ba_pos = fields.Text('Note Berita Acara POS')
    reason_cancel = fields.Text('Cancel Reason')

    
    # Audit Trail 
    post_date = fields.Datetime('Posted on')
    post_uid = fields.Many2one('res.users','Posted by')
    cancel_uid = fields.Many2one('res.users','Cancelled by')
    cancel_date = fields.Datetime('Cancelled on')
    approved_adh_on = fields.Datetime('Approved ADH on')
    approved_adh_uid = fields.Many2one('res.users','Approved ADH by')
    approved_soh_on = fields.Datetime('Approved SOH on')
    approved_soh_uid = fields.Many2one('res.users','Approved SOH by')

    # 9: relation fields
    company_id = fields.Many2one('res.company','Branch')
    cashier_id = fields.Many2one('hr.employee',string='Kasir',domain="[('company_id', '=', company_id)]")
    admin_pos_id = fields.Many2one('hr.employee',string='Admin Pos',domain="[('company_id', '=', company_id)]")
    adh_id = fields.Many2one('hr.employee',string='ADH',domain="[('company_id', '=', company_id)]")
    soh_id = fields.Many2one('hr.employee',string='SOH',domain="[('company_id', '=', company_id)]")
    cash_detail_ids = fields.One2many('tw.cash.count.line','cash_count_id',string='Cash',domain=[('type','=','cash')], context={'default_type':'cash'})
    petty_cash_detail_ids = fields.One2many('tw.cash.count.line','cash_count_id',string='Petty Cash',domain=[('type','=','petty_cash')], context={'default_type':'petty_cash'})
    reimburse_petty_cash_detail_ids = fields.One2many('tw.cash.count.line','cash_count_id',string='Reimburse Petty Cash',domain=[('type','=','reimburse_petty_cash')], context={'default_type':'reimburse_petty_cash'})
    other_receivable_ids = fields.One2many('tw.cash.count.other','cash_count_id','Penerimaan Lain')

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and not record.name and record.state:
                prefix = record.company_id.code
                seq_name = self.env['ir.sequence'].get_sequence_code('CC', prefix)
                record.name = seq_name
    

    @api.onchange('company_id')
    def onchange_branch(self):
        self.cashier_id = False
        self.admin_pos_id = False
        self.adh_id = False
        self.soh_id = False
        if self.company_id:
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            self.cashier_id = branch_setting_obj.cashier_id.id
            self.admin_pos_id = branch_setting_obj.admin_pos_id.id
            self.adh_id = branch_setting_obj.admin_head_id.id
            self.soh_id = branch_setting_obj.branch_head_id.id

    # 12: Override Methods

    @api.model_create_multi
    def create(self,vals_list):
        
        return super(TwCashCount,self).create(vals_list)

    def unlink(self):
        for me in self:
            if me.state != 'draft':
                raise Warning("Data selain draft tidak bisa dihapus !")
        return super(TwCashCount, self).unlink()

    # 13: Action Methods

    def action_update_plafon(self):
        branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
        self.plafon_petty_cash_sr = branch_setting_obj.plafon_petty_cash_sr
        self.plafon_petty_cash_ws = branch_setting_obj.plafon_petty_cash_ws
        self.plafon_petty_cash_atl_btl = branch_setting_obj.plafon_petty_cash_atl_btl

    def action_generate_data(self):
        cash_detail_ids = []
        petty_cash_detail_ids = []
        reimburse_petty_cash_detail_ids = []

        branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
        self.plafon_petty_cash_sr = branch_setting_obj.plafon_petty_cash_sr
        self.plafon_petty_cash_ws = branch_setting_obj.plafon_petty_cash_ws
        self.plafon_petty_cash_atl_btl = branch_setting_obj.plafon_petty_cash_atl_btl

        # Cash
        query_cash = """
            SELECT bt.name
            , bt.date
            , 'posted' as state
            , btl.description
            , btl.amount
            , UPPER(aj.name->>'en_US') as journal
            , aj.id as journal_id 
            FROM tw_bank_transfer bt
            INNER JOIN tw_bank_transfer_line btl ON btl.bank_transfer_id = bt.id
            INNER JOIN account_journal aj ON aj.id = bt.journal_id
            WHERE bt.company_id = %d
            AND bt.state in ('approved','posted')
            AND bt.date = '%s'
            ORDER by bt.name ASC
        """ %(self.company_id.id,self.date)
        self.env.cr.execute(query_cash)
        ress = self.env.cr.dictfetchall()
        for res in ress:
            if 'GC' in res.get('journal'):
                continue
            if self.type_cash_count == 'Showroom':
                if 'POS' in res.get('journal'):
                    continue
            elif self.type_cash_count == 'POS':
                if 'POS' not in res.get('journal'):
                    continue
            cash_detail_ids.append([0,False,{
                'name':res.get('name'),
                'description':res.get('description'),
                'date':res.get('date'),
                'journal_id':res.get('journal_id'),
                'amount':res.get('amount'),
                'journal':res.get('journal'),
                'status':res.get('state','').title(),
            }])

        # Petty Cash
        query_pc = """
            SELECT pc.name
            , pc.date
            , pc.state
            , pcl.name as description
            , pcl.amount_real as amount
            , UPPER(aj.name->>'en_US') as journal
            , aj.id as journal_id 
            FROM tw_petty_cash_out pc
            INNER JOIN tw_petty_cash_out_line pcl ON pcl.petty_cash_out_id = pc.id
            INNER JOIN account_journal aj ON aj.id = pc.journal_petty_id
            WHERE pc.company_id = %d
            AND pc.state = 'posted'
            AND pc.date <= '%s'
            AND aj.type = 'petty_cash'
            AND pcl.amount_real > 0
            ORDER BY pc.name ASC
        """ %(self.company_id.id,self.date)
        self.env.cr.execute(query_pc)
        ress = self.env.cr.dictfetchall()
        for res in ress:
            if 'GC' in res.get('journal'):
                continue
            if self.type_cash_count == 'Showroom':
                if 'POS' in res.get('journal'):
                    continue
            elif self.type_cash_count == 'POS':
                if 'POS' not in res.get('journal'):
                    continue
            petty_cash_detail_ids.append([0,False,{
                'name':res.get('name'),
                'description':res.get('description'),
                'date':res.get('date'),
                'journal_id':res.get('journal_id'),
                'journal':res.get('journal'),
                'status':res.get('state','').title(),
                'amount':res.get('amount'),
            }])

        # Reimburse
        query_rb = """
            SELECT
            r.name
            , r.state
            , r.create_date + interval '7 hours' as create_date
            , r.amount_total
            , UPPER(aj.name->>'en_US') as journal
            , aj.id as journal_id 
            FROM tw_reimbursement_petty_cash r
            INNER JOIN account_journal aj ON aj.id = r.journal_id
            WHERE r.company_id = %d
            AND r.state in ('request','approved')
            AND (r.create_date + interval '7 hours')::date <= '%s'
            AND aj.type = 'petty_cash'
            ORDER BY r.name ASC
         """ %(self.company_id.id,self.date)
        self.env.cr.execute(query_rb)
        ress = self.env.cr.dictfetchall()
        for res in ress:
            if 'GC' in res.get('journal'):
                continue
            if self.type_cash_count == 'Showroom':
                if 'POS' in res.get('journal'):
                    continue
            elif self.type_cash_count == 'POS':
                if 'POS' not in res.get('journal'):
                    continue
            reimburse_petty_cash_detail_ids.append([0,False,{
                'name':res.get('name'),
                'date':res.get('date_request'),
                'journal_id':res.get('journal_id'),
                'journal':res.get('journal'),
                'status':res.get('state','').title(),
                'amount':res.get('amount_total'),       
            }])
        
        self.write({
            'generate_date':self._get_default_datetime(),
            'cash_detail_ids':cash_detail_ids,
            'petty_cash_detail_ids':petty_cash_detail_ids,
            'reimburse_petty_cash_detail_ids':reimburse_petty_cash_detail_ids,    
        })

    
    def action_post(self):
        self.check_validation()
        self.write({
            'post_date':self._get_default_datetime(),
            'post_uid':self._uid,
            'state':'posted',    
        })

    def action_bakso(self):
        form_id = self.env.ref('tw_cash_count.view_tw_cash_count_berita_acara_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Berita Acara',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.cash.count.berita.acara.wizard',
            'context':{'default_cash_count_id':self.id,'default_options':self.type_cash_count},
            'views': [(form_id, 'form')],
            'target':'new'
        }

    def action_cancel(self):
        form_id = self.env.ref('tw_cash_count.view_tw_cash_count_cancel_wizard').id
        return {
            'name': 'Cancel Cash Count',
            'res_model': 'tw.cash.count',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': self.id,
        }

    def action_cancel_submit(self):
        if self.state != 'posted':
            raise Warning('Cash Count tidak bisa dicancel !')
        self.write({
            'state':'cancelled',
            'cancel_uid':self._uid,
            'cancel_date':self._get_default_datetime(),    
        })

    # 14: Private Methods
    def check_validation(self):
        message_error = ''
        if not self.generate_date:
            raise Warning('Silahkan Generate Data Terlebih Dahulu !')
            
        for x in self.cash_detail_ids:
            if not x.validation_id:
                message_error += '\n Data Cash %s' % x.name
        
        for x in self.petty_cash_detail_ids:
            if not x.validation_id:
                message_error += '\n Data Petty Cash %s' % x.name
        
        if message_error:
            raise Warning('Data Cash atau Petty Cash masih ada yang belum di validasi !\n%s' % message_error)
    
    
    




