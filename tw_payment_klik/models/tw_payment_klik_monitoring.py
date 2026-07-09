from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class MonitoringPaymentKlik(models.TransientModel):
    _name = "tw.payment.klik.monitoring"
    _description = "Monitoring Payment Klik"

    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    def _get_default_user(self):
        return self.env.user.id or self._uid

    name = fields.Char('Name',default='Monitoring')
    data_count = fields.Char ( string="Jumlah Data",  help="")
    history_data_count = fields.Char ( string="Jumlah Data (History)",  help="")
    monitoring_type = fields.Selection([
        ('verification','Verification'),
        ('approval','Approval'),
        ('process','Processing'),
    ],'Monitoring Type')
    data_shown = fields.Selection([
        ('open', 'New (akan dioperasikan)'),
        ('all','ALL'),
    ],'Data yang ditampilkan', default='open')
    approval_data_shown = fields.Selection([
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('all','Approved & Rejected'),
    ],'Status Approval', default='approve')

    filter_payment_klik_uid = fields.Many2one('res.users','Payment Klik by',default=_get_default_user)
    history_start_date = fields.Date('Tanggal History Awal')
    history_end_date = fields.Date('Tanggal History Akhir')

    new_verification_state = fields.Selection(string='Set Verification State', selection=[('verify', 'Verify'),])
    new_approval_state = fields.Selection(string='Set Approval State', selection=[('approve', 'Approve'),('reject', 'Reject'),])
    new_process_state = fields.Selection(string='Set Process State', selection=[('process', 'Process'),])
    new_reject_reason = fields.Char('Set Reject Reason')
    new_is_single_click = fields.Boolean('Set Single Click')

    bank_id = fields.Many2one('res.bank', 'Bank')
    line_ids = fields.One2many(comodel_name="tw.payment.klik.monitoring.line", inverse_name="monitoring_id",  string="Monitoring Lines",  help="")
    history_line_ids = fields.One2many(comodel_name="tw.payment.klik.monitoring.line", inverse_name="history_monitoring_id",  string="Monitoring Lines (History)",  help="")

    FINISHED_TRX_STATE = {
        'tw.account.payment': ('paid'),
        'tw.advance.payment': ('paid','done'),
        'tw.settlement': ('done'),
        'tw.bank.transfer': ('approved'),
    }

    @api.onchange('data_shown')
    def onchange_data_shown(self):
        self.history_start_date = False
        self.history_end_date = False

    @api.onchange('new_approval_state')
    def onchange_new_fields(self):
        if self.new_approval_state != 'reject':
            self.new_reject_reason = False

    def action_search(self):
        self.line_ids = False
        self.history_line_ids = False
        target_states = ['draft']
        if self.monitoring_type == 'approval':
            target_states = ['verify','approve_1']
        elif self.monitoring_type == 'process':
            target_states = ['approve','reject']
        dom = [
            ('bank_id','=',self.bank_id.id),
            ('state','in',target_states),
            ('transaction_id','!=',False),
        ]
        if self.filter_payment_klik_uid:
            dom.append(('payment_klik_uid','=',self.filter_payment_klik_uid.id))
        if self.monitoring_type == 'verification':
            dom.append(('verify_date','=',False))
        elif self.monitoring_type == 'approval':
            dom += [
                ('approve_date','=',False),
                ('reject_date','=',False),
            ]
        elif self.monitoring_type == 'process':
            dom.append(('process_date','=',False))
        payment_kliks = self.env['tw.payment.klik.line'].sudo().search(dom)

        line_ids = []
        for pk in payment_kliks:
            if (
                self.monitoring_type == 'process'
                and self.approval_data_shown != 'all'
                and pk.state != self.approval_data_shown
            ):
                continue
            values = {
                'payment_klik_line_id': pk.id,
                'payment_klik_name': pk.payment_klik_id.name,
                'name': pk.name,
                'state': pk.state,
                'paid_amount': float(pk.paid_amount),
                'rek_tujuan': pk.rek_tujuan,
                'bank_tujuan': pk.bank_tujuan,
                'bank_sumber': pk.journal_id.name,
                'is_single_click': pk.is_single_click,
            }
            if self.monitoring_type == 'verification':
                values.update({
                    'verify_date': pk.verify_date,
                    'verify_uid': pk.verify_uid,
                })
            elif self.monitoring_type == 'approval':
                values.update({
                    'approve_date': pk.approve_date,
                    'approve_uid': pk.approve_uid,
                    'reject_date': pk.reject_date,
                    'reject_uid': pk.reject_uid,
                })
            elif self.monitoring_type == 'process':
                values.update({
                    'process_date': pk.process_date,
                    'process_uid': pk.process_uid,
                })
            trx_name = False
            if pk.model_name == 'tw.account.payment':
                trx_name = 'supplier_payment_id'
            elif pk.model_name == 'tw.advance.payment':
                trx_name = 'advance_payment_id'
            elif pk.model_name == 'tw.settlement':
                trx_name = 'settlement_advance_payment_id'
            elif pk.model_name == 'tw.bank.transfer':
                trx_name = 'bank_transfer_id'
            if trx_name and pk.transaction_id:
                record = self.env[pk.model_name].sudo().search([
                    ('id','=',pk.transaction_id),
                ],limit=1)
                if not record or record.state in self.FINISHED_TRX_STATE[pk.model_name]:
                    continue
                values[trx_name] = pk.transaction_id
            line_ids.append([0,False,values])

        self.line_ids = line_ids
        self.line_ids.set_payment_klik_by_if_null()
        self.data_count = "%s data" % str(len(self.line_ids))

        if self.data_shown == 'all':
            history_dom = [
                ('journal_id.name','=',bank_name),
                ('transaction_id','!=',False),
            ]
            if self.filter_payment_klik_uid:
                history_dom.append(('payment_klik_uid','=',self.filter_payment_klik_uid.id))
            if self.monitoring_type == 'verification':
                history_dom.append(('verify_date','!=',False))
                if self.history_start_date:
                    history_dom.append(('verify_date','>=',self.history_start_date))
                if self.history_end_date:
                    history_dom.append(('verify_date','<=',self.history_end_date))
            elif self.monitoring_type == 'approval':
                history_dom += [
                    '|',
                    ('approve_1_date','!=',False),
                    '|',
                    ('approve_date','!=',False),
                    ('reject_date','!=',False),
                ]
                if self.history_start_date:
                    history_dom += [
                        '|',
                        ('approve_1_date','>=',self.history_start_date),
                        '|',
                        ('approve_date','>=',self.history_start_date),
                        ('reject_date','>=',self.history_start_date),
                    ]
                if self.history_end_date:
                    history_dom += [
                        '|',
                        ('approve_1_date','<=',self.history_end_date),
                        '|',
                        ('approve_date','<=',self.history_end_date),
                        ('reject_date','<=',self.history_end_date),
                    ]
            elif self.monitoring_type == 'process':
                history_dom.append(('process_date','!=',False))
                if self.history_start_date:
                    history_dom.append(('process_date','>=',self.history_start_date))
                if self.history_end_date:
                    history_dom.append(('process_date','<=',self.history_end_date))

            history_payment_kliks = self.env['tw.payment.klik.line'].sudo().search(history_dom)
            history_line_ids = []
            for hpk in history_payment_kliks:
                values = {
                    'payment_klik_line_id': hpk.id,
                    'payment_klik_name': hpk.payment_klik_id.name,
                    'name': hpk.name,
                    'state': hpk.state,
                    'paid_amount': float(hpk.paid_amount),
                    'rek_tujuan': hpk.rek_tujuan,
                    'bank_tujuan': hpk.bank_tujuan,
                    'bank_sumber': hpk.journal_id.name,
                    'is_single_click': hpk.is_single_click,
                }
                if self.monitoring_type == 'verification':
                    values.update({
                        'verify_date': hpk.verify_date,
                        'verify_uid': hpk.verify_uid,
                    })
                elif self.monitoring_type == 'approval':
                    values.update({
                        'approve_date': hpk.approve_date,
                        'approve_uid': hpk.approve_uid,
                        'reject_date': hpk.reject_date,
                        'reject_uid': hpk.reject_uid,
                    })
                elif self.monitoring_type == 'process':
                    values.update({
                        'process_date': hpk.process_date,
                        'process_uid': hpk.process_uid,
                    })
                trx_name = False
                if hpk.model_name == 'tw.account.payment':
                    trx_name = 'supplier_payment_id'
                elif hpk.model_name == 'tw.advance.payment':
                    trx_name = 'advance_payment_id'
                elif hpk.model_name == 'tw.settlement':
                    trx_name = 'settlement_advance_payment_id'
                elif hpk.model_name == 'tw.bank.transfer':
                    trx_name = 'bank_transfer_id'
                if trx_name and hpk.transaction_id:
                    record = self.env[pk.model_name].sudo().search([
                        ('id','=',pk.transaction_id),
                    ],limit=1)
                    if not record:
                        continue
                    values[trx_name] = hpk.transaction_id
                history_line_ids.append([0,False,values])

            self.history_line_ids = history_line_ids
            self.history_line_ids.set_payment_klik_by_if_null()
            self.history_data_count = "%s data" % str(len(self.history_line_ids))

    def action_execute(self):
        if not self.line_ids:
            raise Warning('Tidak ada data!')
        this_uid = self.env.user.id or self._uid
        if self.monitoring_type == 'verification':
            if not self.env.user.has_group('tw_report_payment_klik.group_monitoring_payment_klik_verify'):
                raise Warning('Anda tidak memiliki akses untuk melakukan ini!')
            for line in self.line_ids:
                if line.verification_state:
                    if line.payment_klik_line_id.payment_klik_uid.id != this_uid:
                        raise Warning('Verifikasi hanya dapat dilakukan oleh user Payment Klik nya yaitu %s' % line.payment_klik_line_id.payment_klik_uid.partner_id.name)
                    line.payment_klik_line_id.write({
                        'state': line.verification_state,
                        'is_single_click': line.is_single_click,
                        'verify_date': self._get_default_date(),
                        'verify_uid': self._uid,
                    })
        elif self.monitoring_type == 'approval':
            if not self.env.user.has_group('tw_report_payment_klik.group_monitoring_payment_klik_approve'):
                raise Warning('Anda tidak memiliki akses untuk melakukan ini!')
            for line in self.line_ids:
                if line.approval_state:
                    new_state = line.approval_state
                    # * Double Approval check here
                    if line.payment_klik_line_id.state == 'approve':
                        double_appr_on_50_banks = {
                            'BRI': 0,
                            'BCA': 0,
                            'BCAVA': 50000000,
                            'BRILPG': 50000000,
                            'MANDIRI': 50000000,
                            'PERMATA': 50000000,
                        }
                        for bank in double_appr_on_50_banks:
                            if (
                                bank in line.payment_klik_line_id.journal_id.name
                                and line.paid_amount > double_appr_on_50_banks[bank]
                            ):
                                new_state = 'approve_1'
                                break
                    # * End of Double Approval check
                    if self._uid == line.payment_klik_line_id.approve_1_uid.id:
                        raise Warning('Error %s: Approval ke-2 TIDAK boleh dilakukan oleh user yang sama dengan Approval ke-1!\n\nApproval ke-1 oleh: %s' % (
                            line.name,
                            line.payment_klik_line_id.approve_1_uid.name_get()[0][1]))
                    line_vals = {
                        'state': new_state,
                        '%s_date' % new_state: self._get_default_date(),
                        '%s_uid' % new_state: self._uid,
                    }
                    if new_state == 'reject':
                        line_vals['reject_reason'] = line.reject_reason
                    line.payment_klik_line_id.write(line_vals)
        elif self.monitoring_type == 'process':
            if not self.env.user.has_group('tw_report_payment_klik.group_monitoring_payment_klik_process'):
                raise Warning('Anda tidak memiliki akses untuk melakukan ini!')
            for line in self.line_ids:
                if line.process_state:
                    if line.payment_klik_line_id.payment_klik_uid.id != this_uid:
                        raise Warning('Processing hanya dapat dilakukan oleh user Payment Klik nya yaitu %s' % line.payment_klik_line_id.payment_klik_uid.partner_id.name)
                    vals = {
                        'state': 'done',
                        'to_post': True,
                        'process_date': self._get_default_date(),
                        'process_uid': self._uid,
                    }
                    if line.supplier_payment_id:
                        vals['supplier_payment_id'] = line.supplier_payment_id.id
                    elif line.advance_payment_id:
                        vals['advance_payment_id'] = line.advance_payment_id.id
                    elif line.settlement_advance_payment_id:
                        vals['settlement_advance_payment_id'] = line.settlement_advance_payment_id.id
                    elif line.bank_transfer_id:
                        vals['bank_transfer_id'] = line.bank_transfer_id.id
                    line.payment_klik_line_id.write(vals)
        return self.action_search()

    def action_set_all(self):
        vals = {}
        if self.monitoring_type == 'verification':
            vals['verification_state'] = self.new_verification_state
            vals['is_single_click'] = self.new_is_single_click
        elif self.monitoring_type == 'approval':
            vals['approval_state'] = self.new_approval_state
            vals['reject_reason'] = self.new_reject_reason
        elif self.monitoring_type == 'process':
            vals['process_state'] = self.new_process_state
        for line in self.line_ids:
            if (
                self.monitoring_type == 'verification'
                and line.payment_klik_line_id.verify_date
            ):
                continue
            if (
                self.monitoring_type == 'approval'
                and (line.payment_klik_line_id.approve_date or line.payment_klik_line_id.reject_date)
            ):
                continue
            if self.monitoring_type == 'process':
                if (
                    (line.approval_state == 'reject' or line.state == 'reject')
                    or line.payment_klik_line_id.process_date
                ):
                    continue
            line.write(vals)


class ReportPaymentKlikLine(models.TransientModel):
    _name = "tw.payment.klik.monitoring.line"
    _description = "Monitoring Payment Klik Line"

    name = fields.Char(string='Name')
    payment_klik_name = fields.Char(string='Payment Klik')
    verification_state = fields.Selection([('verify', 'Verify'),],string='Verification State')
    approval_state = fields.Selection([('approve','Approve'),('reject','Reject'),],string='Approval State')
    process_state = fields.Selection([('process','Process'),],string='Process State')
    reject_reason = fields.Char('Reject Reason')
    is_single_click = fields.Boolean('Single Click')
    
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('verify', 'Verify'),
        ('approve_1', 'Approved (1 of 2)'),
        ('approve', 'Approved (2 of 2)'),
        ('reject', 'Rejected'),
        ('done', 'Done'),
    ], default='draft')
    paid_amount = fields.Float(string='Paid Amount')
    rek_tujuan = fields.Char(string='Rek Tujuan')
    bank_tujuan = fields.Char(string='Bank Tujuan')
    bank_sumber = fields.Char(string='Bank Sumber')
    
    # * Computed fields
    nama_tujuan = fields.Char('Nama Tujuan', compute='_compute_fields')
    payment_klik_by = fields.Char('Payment Klik by', compute='_compute_fields')
    
    # * Fields used as History Monitoring Payment Klik
    verify_date = fields.Datetime('Verified on')
    verify_uid = fields.Many2one('res.users', 'Verified by')
    approve_1_date = fields.Datetime('#1 Approval on')
    approve_1_uid = fields.Many2one('res.users', '#1 Approval by')
    approve_date = fields.Datetime('#2 Approval on')
    approve_uid = fields.Many2one('res.users', '#2 Approval by')
    reject_date = fields.Datetime('Rejected on')
    reject_uid = fields.Many2one('res.users', 'Rejected by')
    process_date = fields.Datetime('Processed on')
    process_uid = fields.Many2one('res.users', 'Processed by')
    last_approve_date = fields.Datetime('Last Approval on', compute='_compute_fields')
    last_approve_uid = fields.Many2one('res.users', 'Last Approval by', compute='_compute_fields')
    
    # Relational Field
    monitoring_id = fields.Many2one('tw.payment.klik.monitoring','Monitoring Payment Klik')
    history_monitoring_id = fields.Many2one('tw.payment.klik.monitoring','Monitoring Payment Klik (History)')
    payment_klik_line_id = fields.Many2one('tw.payment.klik.line','Payment Klik Line')
    
    # * Transactions (must only be filled one of these at any given time)
    supplier_payment_id = fields.Many2one('tw.account.payment', 'Supplier Payment')
    advance_payment_id = fields.Many2one('tw.advance.payment', 'Advance Payment')
    settlement_advance_payment_id = fields.Many2one('tw.settlement','Settlement Advance Payment')
    bank_transfer_id = fields.Many2one('tw.bank.transfer', 'Bank Transfer')

    def set_payment_klik_by_if_null(self):
        for each in self:
            if not each.payment_klik_line_id.payment_klik_uid:
                pk_uid = False
                if each.supplier_payment_id:
                    pk_uid = each.supplier_payment_id.payment_klik_uid
                elif each.advance_payment_id:
                    pk_uid = each.advance_payment_id.payment_klik_uid
                elif each.settlement_advance_payment_id:
                    pk_uid = each.advance_payment_id.payment_klik_uid
                elif each.bank_transfer_id:
                    pk_uid = each.bank_transfer_id.payment_klik_uid

                if pk_uid:
                    each.payment_klik_line_id.payment_klik_uid = pk_uid

    def _return_letters_only(self,text):
        text = str(text)
        if not text:
            return False
        return text.translate(None,'0123456789,./;:[](){}-_')

    def _compute_fields(self):
        for each in self:
            each.last_approve_date = each.approve_date or each.approve_1_date
            each.last_approve_uid = each.approve_uid or each.approve_1_uid
            if each.supplier_payment_id:
                each.nama_tujuan = each.supplier_payment_id.account_holder or each.supplier_payment_id.partner_bank_id.acc_holder_name
                each.payment_klik_by = each.supplier_payment_id.payment_klik_uid.partner_id.name
                if not each.payment_klik_line_id.payment_klik_uid:
                    each.payment_klik_line_id.payment_klik_uid = each.supplier_payment_id.payment_klik_uid
            elif each.advance_payment_id:
                each.nama_tujuan = each.advance_payment_id.partner_bank_id.acc_holder_name
                each.payment_klik_by = each.advance_payment_id.payment_klik_uid.partner_id.name
                if not each.payment_klik_line_id.payment_klik_uid:
                    each.payment_klik_line_id.payment_klik_uid = each.advance_payment_id.payment_klik_uid
            elif each.settlement_advance_payment_id:
                each.nama_tujuan = each.settlement_advance_payment_id.account_avp_id.partner_bank_id.acc_holder_name
                each.payment_klik_by = each.settlement_advance_payment_id.payment_klik_uid.partner_id.name
                if not each.payment_klik_line_id.payment_klik_uid:
                    each.payment_klik_line_id.payment_klik_uid = each.settlement_advance_payment_id.payment_klik_uid
            elif each.bank_transfer_id:
                each.nama_tujuan = each.bank_transfer_id.partner_bank_id.acc_holder_name
                each.payment_klik_by = each.bank_transfer_id.payment_klik_uid.partner_id.name
                if not each.payment_klik_line_id.payment_klik_uid:
                    each.payment_klik_line_id.payment_klik_uid = each.bank_transfer_id.payment_klik_uid