# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re
from odoo.tools import float_compare

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TwProposal(models.Model):
    _name = "tw.proposal"
    _inherit = ["tw.attachment.mixin"]
    _description = "Proposal Online"


    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
   
    # 8: fields
    name = fields.Char(string='Nomor Proposal',compute='_compute_name',store=True)
    date = fields.Date(string='Tanggal', default=_get_default_date)
    
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    
    code_budget = fields.Char(string='Kode Budget')
    event = fields.Text(string='Keterangan Event')
    
    type_input_proposal = fields.Selection(string='Tipe Input Proposal', selection=[
        ('text_with_image', 'Text with Image'),
        ('text', 'Text Only'),
    ],default='text')

    background = fields.Html(string='Background (Detail)',sanitize=True)
    goals = fields.Html(string='Tujuan (Detail)')
    what = fields.Html(string='What (Detail)')
    how = fields.Html(string='How (Detail)')
    background_text = fields.Text(string='Background')
    goals_text = fields.Text(string='Tujuan')
    what_text = fields.Text(string='What')
    how_text = fields.Text(string='How')
    is_deviation = fields.Boolean(string='Penyimpangan?', default=False)
    is_coo = fields.Boolean(string='Grup COO?', compute="_compute_is_coo")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close','Closed'),
        ('done', 'Done')
    ], default='draft', string='Status')
    
    category = fields.Selection([
        ('recurring','Rutin'),
        ('non_recurring','Tidak Rutin'),
    ], string='category', default='recurring')
    
    budget_state = fields.Selection([
        ('under','Under Budget'),
        ('on','On Budget'),
        ('over','Over Budget'),
    ], string='Status Budget', compute='_compute_amount_remaining', store=True)
    
    # total proposal
    amount_total = fields.Float(string='Total', digits='Product Price', compute='_compute_amount_total', store=True)
    # limit proposal berdasarkan limit approver tertinggi
    amount_approved = fields.Float(string='Total Approved', digits='Product Price')
    # amount_reserved: amount AVP & NC status RFA
    amount_reserved = fields.Float(string='Total Reserved', digits='Product Price', compute='_compute_amount_paid', store=True)
    # amount AVP & NC status approved
    amount_paid = fields.Float(string='Total Paid', digits='Product Price', compute='_compute_amount_paid', store=True)
    amount_remaining = fields.Float(string='Total Sisa', digits='Product Price', compute='_compute_amount_remaining', store=True)
    amount_over = fields.Float(string='Total Over', digits='Product Price', compute='_compute_amount_remaining', store=True)
    amount_total_sponsor = fields.Float(string='Beban Sponsor', digits='Product Price', compute='_compute_amount_sponsor', store=True)
    is_print_prop_ok = fields.Boolean(string='Print Proposal OK?', default=False)
    
    # Audit Trail
    close_uid = fields.Many2one('res.users', string='Closed by', readonly=True)
    close_date = fields.Datetime(string='Closed on', readonly=True)
    done_uid = fields.Many2one('res.users', string='Done by', readonly=True)
    done_date = fields.Datetime(string='Done on', readonly=True)
    

    # 9: relation fields
    pic_id = fields.Many2one('hr.employee', string='PIC', domain="[('company_id','=',company_id)]", ondelete='restrict')
    department_id = fields.Many2one('hr.department', string='Departemen', ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Branch', ondelete='restrict') #
    line_ids = fields.One2many('tw.proposal.line', 'proposal_id', string='Detail')
    sponsor_ids = fields.One2many('tw.proposal.sponsor', 'proposal_id', string='Detail Sponsor')
    schedule_ids = fields.One2many('tw.proposal.schedule', 'proposal_id', string='Schedule')
    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string='Budget Approval',domain=[('model_id','=',_name)])
    payment_ids = fields.One2many('tw.proposal.payment', 'proposal_id', string='Detail Pembayaran')

    # 10: constraints & sql constraints
    @api.constrains('line_ids')
    def _check_empty_line(self):
        if len(self.line_ids) <= 0:
            raise Warning('Perhatian!\nDetail proposal harus diisi.')
    
    # Detail proposal wajib diisi
    @api.constrains('line_ids')
    def _check_empty_line(self):
        if len(self.line_ids) <= 0:
            raise Warning('Perhatian!\nDetail proposal harus diisi.')

    # Jadwal proposal wajib diisi
    @api.constrains('schedule_ids')
    def _check_empty_schedule(self):
        if len(self.schedule_ids) <= 0:
            raise Warning('Perhatian!\nSchedule proposal harus diisi.')

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if not record.name and record.state == 'draft':
                record.name = self.env['ir.sequence'].get_sequence_code('PROPOSAL', str(record.company_id.code))
            else:
                record.name = record.name

    @api.depends('line_ids.amount_total')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(x.amount_total for x in record.line_ids)

    @api.depends('line_ids.amount_reserved','line_ids.amount_paid')
    def _compute_amount_paid(self):
        for record in self:
            record.amount_reserved = sum(x.amount_reserved for x in record.line_ids)
            record.amount_paid = sum(x.amount_paid for x in record.line_ids)

    @api.depends('state','amount_total','amount_reserved','amount_paid')
    def _compute_amount_remaining(self):
        for record in self:
            amount_remaining = record.amount_total - (record.amount_reserved + record.amount_paid)
            if amount_remaining < 0:
                record.amount_remaining = 0
                record.amount_over = abs(amount_remaining)
                if record.state == 'draft':
                    record.budget_state = False
                else:
                    record.budget_state = 'over' 
            elif amount_remaining == 0: 
                record.amount_remaining = amount_remaining
                record.amount_over = 0
                if record.state == 'draft':
                    record.budget_state = False
                else:
                    record.budget_state = 'on'
            else:
                record.amount_remaining = amount_remaining
                record.amount_over = 0
                if record.state == 'draft':
                    record.budget_state = False
                else:
                    record.budget_state = 'under'

    @api.depends('sponsor_ids.amount')
    def _compute_amount_sponsor(self):
        for record in self:
            record.amount_total_sponsor = sum(x.amount for x in record.sponsor_ids)

    def _compute_is_coo(self):
        is_coo_query = """
            SELECT 
                u.id AS user_id,
                emp.id AS employee_id, 
                g.name->>'en_US' AS coo_group
            FROM hr_employee emp
            JOIN resource_resource rr ON emp.resource_id = rr.id
            JOIN res_users u ON rr.user_id = u.id
            JOIN res_groups_users_rel gu ON u.id = gu.uid
            JOIN res_groups g ON gu.gid = g.id
            WHERE g.name->>'en_US' = 'COO'
            AND u.id = %d
        """ % (self._uid)
        self._cr.execute(is_coo_query)
        is_coo = self._cr.fetchone()
        if is_coo:
            self.is_coo = True
        else:
            self.is_coo = False
    
    def _compute_state_done(self):
        for record in self:
            if float_compare(record.amount_paid, record.amount_total, precision_digits=2) >= 0 and record.amount_total > 0:
                record.state = 'done'

    @api.onchange('pic_id')
    def _onchange_department_id(self):
        self.department_id = False
        if self.pic_id and self.pic_id.department_id:
            self.department_id = self.pic_id.department_id.id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('type_input_proposal') == 'text':
                vals['background'] = vals['background_text']
                vals['goals'] = vals['goals_text']
                vals['what'] = vals['what_text']
                vals['how'] = vals['how_text']
        return super(TwProposal, self).create(vals_list)

    def write(self, vals):
        if vals.get('type_input_proposal') == 'text' or self.type_input_proposal == 'text':
            vals['background'] = vals.get('background_text') or self.background_text
            vals['goals'] = vals.get('goals_text') or self.goals_text
            vals['what'] = vals.get('what_text') or self.what_text
            vals['how'] = vals.get('how_text') or self.how_text
        return super(TwProposal, self).write(vals)

    
    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise Warning('Proposal selain status Draft tidak bisa dihapus!')
        return super(TwProposal, self).unlink()

    def copy(self):
        line_ids = []
        sponsor_ids = []
        schedule_ids = []
        for x in self.line_ids:
            line_ids.append([0, 0, {
                'description': x.description,
                'qty': x.qty,
                'price_unit': x.price_unit,
                'amount_total': x.amount_total,
                'pay_to': x.pay_to,
                'supplier_id': x.supplier_id.id,
                'cash_remark': x.cash_remark,
                'amount_reserved': 0,
                'amount_paid': 0,
                'payment_ids': []
            }])
        for x in self.sponsor_ids:
            sponsor_ids.append([0, 0, {
                'supplier_id': x.supplier_id.id,
                'amount': x.amount,
            }])
        for x in self.schedule_ids:
            schedule_ids.append([0, 0, {
                'location': x.location,
                'date_start': x.date_start,
                'date_end': x.date_end,
                'day_count': (x.date_end - x.date_start).days
            }])
        name = self.env['ir.sequence'].get_sequence_code('PROPOSAL', str(self.company_id.code))
        return super(TwProposal, self).copy({
            'name': name,
            'company_id': self.company_id.id,
            'date': date.today(),
            'division': self.division,
            'pic_id': self.pic_id.id,
            'department_id': self.department_id.id,
            'event': self.event,
            'code_budget': self.code_budget,
            'background': self.background,
            'goals': self.goals,
            'what': self.what,
            'how': self.how,
            'state': 'draft',
            'budget_state': False,
            'amount_total': self.amount_total,
            'amount_approved': 0,
            'amount_reserved': 0,
            'amount_paid': 0,
            'amount_remaining': 0,
            'amount_over': 0,
            'amount_total_sponsor': self.amount_total_sponsor,
            'is_print_prop_ok': False,
            'close_uid': False,
            'close_date': False,
            'line_ids': line_ids,
            'sponsor_ids': sponsor_ids,
            'schedule_ids': schedule_ids,
            'attachment_ids': [],
            'approval_ids': [],
            'payment_ids': []
        })

    # 13: action methods
    def action_proposal_list(self):
        tree_id = self.env.ref('tw_proposal.view_tw_proposal_list').id
        form_id = self.env.ref('tw_proposal.view_tw_proposal_form').id
        search_view_id = self.env.ref('tw_proposal.view_tw_proposal_filter').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Proposal',
            'view_mode': 'list,form',
            'res_model': 'tw.proposal',
            'views': [(tree_id, 'list'), (form_id, 'form')],
            'search_view_id': search_view_id,
            'context': {'readonly_by_pass': 1, 'search_default_rfa': 1}
        }

    
    def action_done(self):
        self.write({
            'state':'done',
            'done_uid': self._uid,
            'done_date': self._get_default_date()
        })
    
    def action_close_proposal(self):
        # Kalau sudah confirm all
        self.write({
            'state': 'close',
            'close_uid': self._uid,
            'close_date': self._get_default_date()
        })

    def action_reject(self):
        form_id = self.env.ref('tw_approval.tw_approval_reject_wizard_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.approval',
            'name': 'Reject Proposal',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'context': {
                'model_name': 'tw.proposal',
                'update_value': {'state': 'draft'}
            },
        }

    def action_print_proposal(self):
        active_ids = self.env.context.get('active_ids', [])
        user = self.env['res.users'].suspend_security().browse(self._uid).name
        datas = {
             'ids': active_ids,
             'model': 'tw.proposal',
             'form': self.read()[0],
             'user': user
        }
        return self.env['report'].suspend_security().render(self, 'tw_proposal.print_proposal_pdf', data=datas)
    
    def action_print_proposal(self):
        self.ensure_one()
        return self.env.ref('tw_proposal.action_proposal_report').report_action(self.id)

    # 14: private methods
    def validation_rfa(self):
        if self.amount_total <= 0:
            raise Warning('Total proposal tidak boleh 0 atau kurang dari 0')

    def get_proposal_amounts_by_pay_to(self, pay_to):
        """
        Calculate total, paid, and reserved amounts for a specific pay_to category.
        """
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.pay_to == pay_to)
        total = sum(l.amount_total for l in lines)
        paid = sum(l.amount_paid for l in lines)
        reserved = sum(l.amount_reserved for l in lines)
        return total, paid, reserved
