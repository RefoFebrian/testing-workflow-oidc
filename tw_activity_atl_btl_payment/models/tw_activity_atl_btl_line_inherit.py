# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime, date
import calendar
import itertools
from lxml import etree

# 2: imports of odoo
from odoo import models, fields, exceptions, api, _, Command
from odoo.exceptions import ValidationError as Warning

# 3: imports of odoo 

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class PaymentActivityATLBTL(models.Model):
    _name = "tw.activity.atl.btl.line"
    _inherit = ["tw.activity.atl.btl.line", "tw.attachment.mixin"]

    state = fields.Selection(selection_add=[('settlement', 'Settlement')])
    
    expense_amount = fields.Float('Claim Amount', compute='_compute_claim_expense', store=True)
    support_fund_amount = fields.Float('Support Fund Amount', compute='_compute_support_fund', store=True)
    actual_expense_amount = fields.Float('Actual Expense Amount')
    total_tax_amount = fields.Float('Total Tax', compute='_compute_total_tax', store=True)

    total_ho_expense = fields.Float('Total HO Expense', compute='_compute_claim_expense', store=True)
    total_leasing_expense = fields.Float('Total Leasing Expense', compute='_compute_claim_expense', store=True)
    total_company_expense = fields.Float('Total Company Expense', compute='_compute_claim_expense', store=True)
    total_support_fund_expense = fields.Float('Total Support Fund Expense', compute='_compute_support_fund', store=True)

    advance_payment_ids = fields.Many2many('tw.advance.payment', relation='tw_activity_atl_btl_line_avp_rel', string='Advance Payments')
    payment_request_ids = fields.Many2many('tw.payment.request', relation='tw_activity_atl_btl_line_nc_rel', string='Payment Requests')
    settlement_ids = fields.Many2many('tw.settlement', relation='tw_activity_atl_btl_line_stl_rel', string='Settlements')

    create_avp_date = fields.Datetime('Create AVP on')
    create_avp_uid = fields.Many2one('res.users', 'Create AVP by')
    create_nc_date = fields.Datetime('Create NC on')
    create_nc_uid = fields.Many2one('res.users', 'Create NC by')
    create_stl_date = fields.Datetime('Create STL on')
    create_stl_uid = fields.Many2one('res.users', 'Create STL by')

    @api.depends('detail_cost_ids.amount', 'detail_cost_ids.expense_source_id')
    def _compute_claim_expense(self):
        for rec in self:
            rec.total_ho_expense = sum(rec.detail_cost_ids.filtered(lambda x: x.expense_source_id.name == 'HO').mapped('amount'))
            rec.total_leasing_expense = sum(rec.detail_cost_ids.filtered(lambda x: x.expense_source_id.name == 'Leasing').mapped('amount'))
            rec.total_company_expense = sum(rec.detail_cost_ids.filtered(lambda x: x.expense_source_id.name == 'Cabang').mapped('amount'))
            rec.expense_amount = rec.total_ho_expense + rec.total_leasing_expense + rec.total_company_expense

    @api.depends('detail_cost_ids.tax_amount')
    def _compute_total_tax(self):
        for rec in self:
            rec.total_tax_amount = sum(rec.detail_cost_ids.mapped('tax_amount'))

    @api.depends('detail_cost_ids.amount', 'detail_cost_ids.expense_source_id')
    def _compute_support_fund(self):
        for rec in self:
            rec.total_support_fund_expense = sum(rec.detail_cost_ids.filtered(lambda x: x.expense_source_id.name == 'Dana Bantuan').mapped('amount'))
            rec.support_fund_amount = rec.total_support_fund_expense

    def action_confirm_lpj(self):
        has_avp = bool(self.advance_payment_ids)

        if has_avp and not self.settlement_ids:
            raise Warning(_('Tolong lakukan Settlement terlebih dahulu sebelum melakukan Confirm LPJ.'))

        super().action_confirm_lpj()

    def action_open_activity(self):
        res = super().action_open_activity()
        for rec in self:
            if rec.state == 'open' and (not rec.advance_payment_ids or not rec.payment_request_ids):
                rec.action_create_advance_payment() 
        return res or True

    def action_create_advance_payment(self):
        """
        Create AVP or NC documents for ATL BTL activity, grouped by Vendor and Source Type.
        """
        self.ensure_one()

        if not self.detail_cost_ids:
            raise Warning(_('Detail Biaya belum diisi.'))

        # Group lines by (Source Type, Expense Source record, Vendor)
        groups = {}
        for line in self.detail_cost_ids:
            if line.subtotal <= 0:
                continue
            
            source_type = line.expense_source_id.expense_source_id.value  # 'AVP' or 'NC'
            if not source_type:
                continue

            vendor_id = line.partner_id.id
            if not vendor_id:
                raise Warning(_(f"Vendor pada baris biaya '{line.note or 'Tanpa Note'}' harus diisi."))

            expense_source = line.expense_source_id  # tw.master.expense.source record
            key = (source_type, expense_source.id, vendor_id)
            if key not in groups:
                groups[key] = {'lines': [], 'expense_source': expense_source}
            groups[key]['lines'].append(line)

        if not groups:
            return

        company = self.company_id
        branch_conf = company.branch_setting_id.account_setting_id if company.branch_setting_id else False
        
        avp_ids = []
        nc_ids = []

        for (source_type, expense_source_id, vendor_id), group_data in groups.items():
            lines = group_data['lines']
            expense_source = group_data['expense_source']
            total_amount = sum(l.subtotal for l in lines)
            vendor = self.env['res.partner'].browse(vendor_id)
            desc = _(f'{"Advance Payment" if source_type == "AVP" else "Payment Request"} for {self.name} - {vendor.name}')

            doc = False
            if source_type == 'AVP':
                if not branch_conf or not branch_conf.journal_avp_id:
                    raise Warning(_(f'Konfigurasi Journal Advance Payment belum dibuat pada Cabang {company.name} !'))
                journal = branch_conf.journal_avp_id
                
                debit_account_id = journal.default_debit_account_id.id or journal.default_account_id.id
                
                vals = {
                    'company_id': company.id,
                    'type': 'advance_payment',
                    'payment_type': 'outbound',
                    'division': 'Unit',
                    'partner_id': vendor_id,
                    'employee_id': self.pic_id.id,
                    'journal_id': journal.id,
                    'account_avp_id': debit_account_id,
                    'due_date': self.start_date or date.today(),
                    'amount': total_amount,
                    'description': desc,
                    'line_dr_ids': [Command.create({
                        'account_id': debit_account_id,
                        'name': desc,
                        'amount': total_amount,
                        'partner_id': vendor_id,
                    })],
                }
                doc = self.env['tw.advance.payment'].create(vals)
                avp_ids.append(doc.id)
                if doc:
                    for line in lines:
                        binary_data = line._get_upload_file_data()
                        if binary_data:
                            self.env['tw.attachment'].create({
                                'name': line.upload_filename or desc,
                                'datas': binary_data,
                                'res_model': doc._name,
                                'res_id': doc.id,
                                'type': 'binary',
                            })

                if hasattr(doc, 'action_request_approval'):
                    doc.action_request_approval()

            elif source_type == 'NC':
                if not branch_conf or not branch_conf.journal_payment_request_id:
                    raise Warning(_(f'Konfigurasi Journal Payment Request belum dibuat pada Cabang {company.name} !'))
                journal = branch_conf.journal_payment_request_id
                
                # Use account from expense source master if set, else fall back to journal default
                line_account_id = (
                    expense_source.account_id.id
                    or journal.default_debit_account_id.id
                    or journal.default_account_id.id
                )
                
                vals = {
                    'company_id': company.id,
                    'type': 'payment_request',
                    'payment_type': 'outbound',
                    'division': 'Unit',
                    'partner_id': vendor_id,
                    'journal_id': journal.id,
                    'due_date': self.start_date if self.start_date > date.today() else date.today(),
                    'amount': total_amount,
                    'memo': desc,
                    'line_dr_ids': [Command.create({
                        'account_id': line_account_id,
                        'name': desc,
                        'amount': total_amount,
                        'partner_id': vendor_id,
                    })],
                }
                doc = self.env['tw.payment.request'].create(vals)
                nc_ids.append(doc.id)
                if doc:
                    for line in lines:
                        binary_data = line._get_upload_file_data()
                        if binary_data:
                            self.env['tw.attachment'].create({
                                'name': line.upload_filename or desc,
                                'datas': binary_data,
                                'res_model': doc._name,
                                'res_id': doc.id,
                                'type': 'binary',
                            })

                if hasattr(doc, 'action_request_approval'):
                    doc.action_request_approval()

        self.write({
            'advance_payment_ids': [Command.set(avp_ids)],
            'payment_request_ids': [Command.set(nc_ids)],
            'create_avp_date': fields.Datetime.now() if avp_ids else False,
            'create_avp_uid': self.env.uid if avp_ids else False,
            'create_nc_date': fields.Datetime.now() if nc_ids else False,
            'create_nc_uid': self.env.uid if nc_ids else False,
        })
        
    def action_create_settlement_from_wizard(self, wizard):
        """
        Called from wizard. Creates one tw.settlement per AVP wizard line.
        Each settlement gets its own actual_amount and attachments.
        """
        self.ensure_one()

        if not self.pic_id:
            raise Warning(_('PIC harus diisi pada activity line sebelum membuat Settlement.'))
        if not self.company_id:
            raise Warning(_('Cabang (company) dibutuhkan pada activity line!'))

        company = self.company_id
        branch_conf = company.branch_setting_id.account_setting_id if company.branch_setting_id else False

        if not branch_conf or not branch_conf.journal_settlement_id:
            raise Warning(_(
                f'Konfigurasi Journal Settlement belum dibuat pada Cabang {company.name}!'
            ))
        if not branch_conf.account_activity_id:
            raise Warning(_(
                f'Konfigurasi Account Activity Plan belum dibuat pada Cabang {company.name}!'
            ))

        settlement_ids = []

        for wiz_line in wizard.line_ids:
            avp = wiz_line.advance_payment_id
            actual = wiz_line.actual_amount

            # Validation per line
            if not avp:
                raise Warning(_('Setiap baris harus memiliki AVP yang terhubung.'))
            if avp.state != 'confirm':
                raise Warning(_(
                    f'AVP dengan Nomor {avp.name} harus berada pada status Confirm sebelum membuat Settlement.'
                ))
            if actual <= 0.0:
                raise Warning(_(
                    f'Actual Amount untuk AVP dengan Nomor {avp.name} harus lebih besar dari nol.'
                ))

            # Determine settlement type (kembali / tambah / False)
            stl_type = False
            if actual < avp.amount:
                stl_type = 'kembali'
            elif actual > avp.amount:
                stl_type = 'tambah'

            description = _(
                'Settlement for ATL/BTL %s - %s (%s to %s)'
            ) % (
                self.name or '',
                self.activity_id.name or '',
                self.start_date or '',
                self.end_date or '',
            )

            # Settlement lines
            line_vals = [(0, 0, {
                'company_id': company.id,
                'account_id': branch_conf.account_activity_id.id,
                'amount': actual,
            })]

            # Attachments from this wizard line
            docs_vals = []
            for attachment in wiz_line.attachment_ids:
                docs_vals.append((0, 0, {
                    'company_id': company.id,
                    'name': attachment.name,
                    'datas': attachment.datas,
                    'description': attachment.description or attachment.name,
                }))

            vals = {
                'advance_payment_id': avp.id,
                'employee_id': self.pic_id.id,
                'company_id': company.id,
                'division': avp.division,
                'amount_avp': avp.amount,
                'account_avp_id': avp.account_avp_id.id,
                'description': description,
                'email': getattr(self.pic_id, 'work_email', False) or False,
                'type': stl_type,
                'settlement_line_ids': line_vals,
                'attachment_ids': docs_vals,
            }

            if stl_type == 'kembali':
                vals['return_journal_id'] = branch_conf.journal_settlement_id.id

            settlement = self.env['tw.settlement'].create(vals)
            settlement.action_confirm()
            settlement_ids.append(settlement.id)

        # Link all settlements back — use the first as primary, or extend to Many2many
        # Here we assume settlement_id stays Many2one → link last or first created
        self.action_history_result()
        self.write({
            'settlement_ids': [Command.set(settlement_ids)],
            'state': 'settlement',
            'create_stl_date': fields.Datetime.now(),
            'create_stl_uid': self.env.user.id,
        })

    def action_settlement(self):
        # Pre-create wizard record so default_get populates lines
        wizard = self.env['tw.activity.settlement.wizard'].with_context(active_id=self.id).create({'activity_line_id': self.id})
        form_id = self.env.ref('tw_activity_atl_btl_payment.tw_activity_settlement_wizard_form_view').id

        return {
            'name': _('Settlement - Actual Amount per AVP'),
            'res_model': 'tw.activity.settlement.wizard',
            'type': 'ir.actions.act_window',
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }
        
    def action_settlement_list(self):
        list_id = self.env.ref('tw_activity_atl_btl_payment.tw_activity_atl_btl_settlement_list_view')
        record_ids = self.env['tw.activity.atl.btl.line'].search([('state', '=', 'confirmed')])

        domain = [('id', 'in', record_ids.ids)]

        user = self.env.user
        employee = user.employee_id
        job_obj = employee.job_id
        sales_force_id = job_obj.sales_force_id
        # TODO: Comment temporary for checking if LPJ menu only show based on ir.rule
        # if sales_force_id and sales_force_id.value in ('sales_coordinator', 'area_manager'):
        #     # Team members = subordinates in HR hierarchy
        #     team_ids = employee.child_ids.ids  # direct reports
        #     domain += [('pic_id', 'in', team_ids + [employee.id])]
        # else:
        #     # Regular employee: only own records
        #     domain += [('pic_id', '=', employee.id)]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.activity.atl.btl.line',
            'name': 'Settlement Activity Plan',
            'view_mode': 'list',
            'view_type': 'form',
            'domain': domain,
            'views': [(list_id.id, 'list')],
        }

    def action_view_avp(self):
        self.ensure_one()
        if not self.advance_payment_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Tidak ada AVP Reference yang terhubung dengan Activity ATL/BTL ini.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Advance Payment'),
            'res_model': 'tw.advance.payment',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'form_view_ref': 'tw_activity_atl_btl_payment.tw_advance_payment_form_view',
            }
        }
        if len(self.advance_payment_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.advance_payment_ids.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', self.advance_payment_ids.ids)],
            })
        return action

    def action_view_nc(self):
        self.ensure_one()
        if not self.payment_request_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Tidak ada NC Reference yang terhubung dengan Activity ATL/BTL ini.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Payment Request'),
            'res_model': 'tw.payment.request',
            'view_mode': 'list,form',
            'target': 'current',
            # context or view ref if needed
        }
        if len(self.payment_request_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.payment_request_ids.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', self.payment_request_ids.ids)],
            })
        return action

    def action_view_stl(self):
        self.ensure_one()
        if not self.settlement_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Tidak ada STL Reference yang terhubung dengan Activity ATL/BTL ini.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Settlement'),
            'res_model': 'tw.settlement',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'form_view_ref': 'tw_activity_atl_btl_payment.tw_settlement_form_view',
            }
        }
        if len(self.settlement_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.settlement_ids.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', self.settlement_ids.ids)],
            })
        return action

