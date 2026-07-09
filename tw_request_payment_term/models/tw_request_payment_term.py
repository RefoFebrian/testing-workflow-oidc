# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3: imports of odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwRequestPaymentTerm(models.Model):
    _name = "tw.request.payment.term"
    _description = "Request Payment Term"
    _order = "id desc"

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ]
    TRANSACTION_TYPE = [
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
    ]

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False 

    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), string='Division', required=True, change_default=True)
    state = fields.Selection(selection=STATE_SELECTION, string='Status', default='draft', copy=False)
    date = fields.Date(string='Date', default=datetime.now().date())
    trans_type = fields.Selection(selection=TRANSACTION_TYPE, string='Transaksi', required=True, default='sales')

    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Approved by")
    confirm_date = fields.Datetime('Approved on')

    # 9: Relational Fields
    company_id = fields.Many2one('res.company', string="Branch", ondelete='restrict', default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    current_payment_term_id = fields.Many2one('account.payment.term', string="Current Payment Term", readonly=True, compute="_compute_current_payment_term", store=True)
    payment_term_id = fields.Many2one('account.payment.term', string="New Payment Term",required=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and not record.name and record.state:
                seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code('RPT', record.company_id.code)
                record.name = seq_name

    @api.depends('partner_id', 'trans_type')
    def _compute_current_payment_term(self):
        for record in self:
            payment_type = record.partner_id.property_payment_term_id
            if record.trans_type == 'purchase':
                payment_type = record.partner_id.property_supplier_payment_term_id

            record.current_payment_term_id =  payment_type or False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.new(vals)._check_duplicate()

        return super().create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_('Only draft records can be deleted. Please cancel the record first.'))
            return super().unlink()

    # 13: action methods
    def action_confirm(self):
        self.ensure_one()
        if self.partner_id and self.payment_term_id:
            if self.trans_type == 'sales':
                self.partner_id.property_payment_term_id = self.payment_term_id
            elif self.trans_type == 'purchase':
                self.partner_id.property_supplier_payment_term_id = self.payment_term_id
            else:
                pass
            
        vals = {
            'confirm_date': fields.Datetime.now(),
            'confirm_uid': self.env.user.id,
            'state' : "confirm"
            }
        self.write(vals)

    # 14: private methods
    def _check_duplicate(self):
        for record in self:
            if not record.partner_id:
                continue

            domain = [
                ('partner_id', '=', record.partner_id.id),
                ('state', '=', 'draft'),
                ('id', '!=', record.id or 0)
            ]
            duplicate = self.search(domain)
            if duplicate:
                messages = [
                    f"- {d.name} pada tanggal {d.date.strftime('%d-%m-%Y')} ({d.state})"
                    for d in duplicate
                ]
                raise Warning("Sudah ada pengajuan yang sama, silahkan cek:\n" + "\n".join(messages))
