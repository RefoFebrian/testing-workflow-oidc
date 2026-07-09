# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.osv import expression
from odoo.exceptions import UserError as Warning, AccessError
from odoo.tools import format_datetime, format_date, format_list, groupby, SQL
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.tools.misc import formatLang

# 5: local imports

# 6: Import of unknown third party lib


class InheritStockPickingAsset(models.Model):
    _name = "tw.good.receive"
    _inherit = ["stock.picking","tw.attachment.mixin"]
    _description = "Good Receive Asset"
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    def _get_new_state_selection(self):
        return [
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('partial_invoiced', 'Partial Invoiced'),
            ('invoiced', 'Invoiced'),
            ('cancel', 'Cancelled'),
            ('done', 'Done')
        ]

    # 8: fields
    name = fields.Char('Name', compute='_compute_name', store=True)
    is_asset = fields.Boolean(string="Is Asset", default=False)
    transaction_type = fields.Char(string='Transaction Type')
    type = fields.Char(string='Type')
    date = fields.Date(string='Date',default=_get_default_date)
    date_document = fields.Date(string='Document Date',default=_get_default_date)
    vendor_picking_number = fields.Char(string='Nomor Surat Jalan Vendor',help="Used to koprol integration")
    entry_count = fields.Integer(compute='_entry_count', string='# Asset Entries')
    note = fields.Text(string='Note')
    notes = fields.Html('Terms and Conditions')
    # Override stock.picking state with custom selection using selection_add
    # Note: approval states (waiting_for_approval, approved) added by separate module
    state = fields.Selection(
        selection_add=[
            ('open', 'Open'),
            ('cancel', 'Cancelled')
        ],
        ondelete={'open': 'set default',
                    'cancel': 'set default'},
        default='draft',
        tracking=True,
        copy=False
    )


    # * Amounts Fields 
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    amount_untaxed = fields.Float(string='Untaxed Amount', compute='_compute_amount_all', digits='Account', store=True)
    amount_tax = fields.Float(string='Taxes', compute='_compute_amount_all', digits='Account', store=True)
    amount_total = fields.Float(string='Total', compute='_compute_amount_all', digits='Account', store=True)
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count', string='Purchase Order Count')

    # * Audit Trail
    rfa_date = fields.Datetime('RFA on')
    rfa_uid = fields.Many2one('res.users',string="RFA by")
    
    confirm_date = fields.Datetime('Confirm on')
    confirm_uid = fields.Many2one('res.users',string="Confirm by")
    
    invoiced_date = fields.Datetime('Invoiced on')
    invoiced_uid = fields.Many2one('res.users',string="Invoiced by")
    
    partial_invoiced_date = fields.Datetime('Partial Invoiced on')
    partial_invoiced_uid = fields.Many2one('res.users',string="Partial Invoiced by")
    
    cancel_date = fields.Datetime('Cancelled on')
    cancel_uid = fields.Many2one('res.users',string="Cancelled by")

    # 9: relation fields   
    move_asset_ids = fields.One2many('tw.good.receive.asset.line', 'picking_id', string="Asset Stock Moves", copy=True)
    account_move_id = fields.Many2one('account.move', string='Account Move', ondelete='cascade')
    account_move_ids = fields.One2many(related='account_move_id.line_ids', string='Journal Items', readonly=True)
    purchase_id = fields.Many2one(string='Purchase Order')
    purchase_order_ids = fields.Many2many('purchase.order.asset', compute='_compute_purchase_order_count', string='Purchase Orders')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods    
    @api.onchange('location_id')
    def _onchange_location_id(self):
        super(InheritStockPickingAsset, self)._onchange_location_id()
        self.move_asset_ids.location_id = self.location_id

    def _compute_amount_all(self):
        for order in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0

            for add in order.move_asset_ids:
                amount_untaxed += add.subtotal
                amount_tax += add.price_tax
                amount_total += add.price_total

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = amount_total
    
    @api.depends_context('lang')
    @api.depends('move_asset_ids.price', 'move_asset_ids.discount')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.company_id:
                order.tax_totals = order._empty_tax_totals(order.company_id.currency_id)
                continue

            order_lines = order.move_asset_ids
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.company_id.currency_id,
                company=order.company_id,
            )
    
    @api.onchange('company_id')
    def _onchange_company_id_asset(self):
        """ Set the picking type based on the company_id """
        if self.company_id:
            if self.is_asset:
                self.picking_type_id = self.picking_type_id.get_picking_type_asset('incoming', self.company_id.id, 'Umum')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Set the picking type based on the partner_id """
        if self.partner_id:
            self.move_asset_ids = False
    
    @api.depends('move_asset_ids.account_move_id')
    def _entry_count(self):
        for asset in self:
            res = self.env['tw.good.receive.asset.line'].search_count([('picking_id', '=', asset.id), ('account_move_id', '!=', False)])
            asset.entry_count = res or 0
    
    @api.depends('move_asset_ids.purchase_order_id')
    def _compute_purchase_order_count(self):
        for record in self:
            pos = record.move_asset_ids.mapped('purchase_order_id')
            record.purchase_order_ids = pos
            record.purchase_order_count = len(pos)

    @api.depends('company_id')
    def _compute_name(self):
        for item in self:
            item.name = self.env['ir.sequence'].get_sequence_code('GR', str(item.company_id.code))

    @api.depends('move_ids.state', 'move_ids.picked')
    def _compute_state(self):
        """
        Override stock.picking's _compute_state to bypass automatic state computation.
        tw.good.receive uses its own state management (draft -> open -> done),
        not based on stock.move states.
        """
        # Do nothing - state is managed manually for tw.good.receive
        pass

    # 12: override methods
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        domain = args or []
        match_domain = []
        is_asset = self._context.get('is_asset',False)
        if name:
            match_domain = ['|',('name', operator, name),('origin', operator, name)]
            if is_asset:
                match_domain = ['|',('name', operator, name), ('product_id.name', operator, name)]
            
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                match_domain = ['&', '!'] + match_domain[1:]
        
        picking = self.search_fetch(expression.AND([domain, match_domain]), ['name'], limit=limit)
        search = picking.name_get()
        
        if is_asset:
            search = []
            for asset in picking.sudo():
                if asset.move_asset_ids:
                    product_names = ", ".join(asset.move_asset_ids.mapped('product_id.name'))
                    search.append((asset.id, f"[{asset.name}] {product_names}"))
                else:
                    search.append((asset.id, f"[{asset.name}]"))
        
        return search

    def name_get(self):
        result = []
        is_asset = self._context.get('is_asset', False)
        for record in self:
            if is_asset and record.move_asset_ids:
                product_names = ", ".join(record.move_asset_ids.mapped('product_id.name'))
                name = f"[{record.name}] {product_names}"
            else:
                name = record.name if record.name else ''
            result.append((record.id, name))
        return result
    
    @api.model_create_multi
    def create(self,vals_list):
        create = super(InheritStockPickingAsset, self).create(vals_list)
        for record in create:
            # Give sequence name
            company_id = record.company_id.id
            branch_obj = self.env['res.company'].browse(company_id)
            if record.is_asset:
                seq_name = self.with_company(company_id).env['ir.sequence'].get_sequence_code('GR', branch_obj.code)
                record.name = seq_name 
            
                if not record.move_asset_ids:
                    raise Warning('GR Asset harus ada minimal 1 item asset yang diterima')
        
        return create
    
    def get_formview_action(self, access_uid=None):
        """ Override this method to add access control for user form view """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_asset_management.group_good_receive_asset_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    
    # TODO: Delete if the transaction requires delete
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning(_('Warning! \nCannot delete records with a state other than draft!'))

        return super(InheritStockPickingAsset, self).unlink()

    # 13: action methods
    def action_view_purchase_orders(self):
        self.ensure_one()
        pos = self.purchase_order_ids
        
        list_view = self.env.ref('tw_asset_management.tw_purchase_order_asset_list_view', False)
        form_view = self.env.ref('tw_asset_management.tw_inherit_purchase_order_asset_form_view', False)
        
        action = {
            'name': _('Purchase Orders Asset'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.asset',
            'view_mode': 'list,form',
            'domain': [('id', 'in', pos.ids)],
            'context': dict(self.env.context, is_asset=True, default_is_asset=True),
        }
        if len(pos) == 1:
            action['views'] = [(form_view and form_view.id or False, 'form')]
            action['res_id'] = pos.id
        else:
            action['views'] = [
                (list_view and list_view.id or False, 'list'),
                (form_view and form_view.id or False, 'form')
            ]
        return action

    def action_open(self):
        """
        Confirm GR:
        - Create stock move untuk setiap line
        - Update qty received di PO
        - Create journal JGR
        - TIDAK membuat asset (dipindah ke Akuisisi)
        """

        if self.state != 'approved':
                raise Warning(f'Silakan refresh halaman Good Receive ini, karena state sudah {self._get_state_value()}')
        
        # Validate: CIP products must have is_asset=True
        for asset in self.move_asset_ids:
            if asset.asset_category_id and asset.asset_category_id.is_cip and not asset.product_id.is_asset:
                raise Warning(_(
                    "Product '%s' memiliki Asset Category CIP tapi checkbox 'Is Asset?' di Product belum dicentang. "
                    "Silahkan centang 'Is Asset?' di menu Products > Tab Assets terlebih dahulu."
                ) % asset.product_id.display_name)
        
        for asset in self.move_asset_ids:
            # Create stock move
            asset.sudo().create_move_by_asset()
            asset.sudo().action_open()
            
            # Update PO status
            asset.purchase_order_id.sudo().action_check_received()
            asset.sudo().update_qty_received()

        # Create Journal JGR
        self.sudo()._create_account_asset_move()
        
        self.write({
            'state': 'open',
            'confirm_date': datetime.now(),
            'confirm_uid': self.env.user.id
        })
    
    def action_done(self):
        if self.state == 'done':
            raise Warning(f'Silakan refresh halaman Good Receive Asset ini, karena state sudah {self._get_state_value()}')
        
        return self.write({
            'state': 'done'
        })

    def action_cancel(self):
        """
        Cancel GR:
        - Cek apakah ada akuisisi yang sudah terbentuk
        - Jika ada, tidak boleh cancel (harus cancel akuisisi dulu)
        - Reverse journal JGR
        - Reset qty received di PO
        """
        
        for record in self:
            if record.state not in ['open', 'draft']:
                raise Warning(_("Hanya bisa cancel GR yang masih Draft atau Open!"))
            
            # Cek apakah ada akuisisi yang sudah terbentuk
            acquired_lines = record.move_asset_ids.filtered(lambda l: l.is_acquired)
            if acquired_lines:
                raise Warning(_("Tidak bisa cancel GR karena sudah ada Akuisisi. Silahkan cancel Akuisisi terlebih dahulu."))
            
            # Reverse journal JGR jika ada
            if record.account_move_id and record.account_move_id.state == 'posted':
                record.account_move_id._reverse_moves(
                    default_values_list=[{
                        'ref': _('Reversal of: %s - GR Cancelled') % record.account_move_id.ref,
                        'date': fields.Date.today(),
                    }],
                    cancel=True
                )
            
            # Reset qty received di PO lines
            for line in record.move_asset_ids:
                if line.purchase_order_line_id:
                    new_qty = line.purchase_order_line_id.qty_received - line.qty
                    line.purchase_order_line_id.qty_received = max(0, new_qty)
                line.state = 'draft'
            
            record.write({
                'state': 'cancel',
                'cancel_date': datetime.now(),
                'cancel_uid': self.env.user.id
            })
        
        return True

    def action_set_to_draft(self):
        """
        Reset GR ke draft setelah cancel.
        """
        for record in self:
            if record.state != 'cancel':
                raise Warning(_("Hanya bisa reset ke draft dari status Cancel!"))
            
            record.write({'state': 'draft'})
        
        return True

    def action_open_entries(self):
        move_ids = []
        for asset in self:
            for data in asset.move_asset_ids:
                if data.account_move_id:
                    move_ids.append(data.account_move_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }

    # 14: private methods 
    def _set_scheduled_date(self):
        for picking in self:
            picking.move_ids.write({'date': picking.date})
    
    def _create_account_asset_move(self):
        if self.account_move_id:
            raise Warning(_("Good Receive already received or Journal Entry already created."))
        self._check_branch_config()
        branch_conf = self.company_id.branch_setting_id.account_setting_id
        currency_id = self.company_id.currency_id.id
        
        journal = branch_conf.journal_good_receive_asset_id
        if self.move_asset_ids:
            first_line = self.move_asset_ids[0]
            if first_line.is_cip:
                journal = branch_conf.journal_good_receive_cip_id
            elif first_line.type_assets == 'asset_prepayments':
                journal = branch_conf.journal_good_receive_prepaid_id

        if not journal:
            raise Warning("Konfigurasi Journal Good Receive untuk tipe aset ini belum dibuat di Branch Config!")

        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'partner_id': self.partner_id.id,
            'currency_id': currency_id,
            'partner_bank_id': False,
            'line_ids': [
                Command.create(line_vals)
                for line_vals in self._prepare_move_line_default_vals()
            ],
        }
        if self.name:
            move_vals['name'] = self.env['ir.sequence'].get_sequence_code('JGR', str(self.company_id.code))

        move_created = self.env['account.move'].sudo().create([move_vals])
        
        move_created.sudo().action_post()
        
        self.account_move_id = move_created.id
    
    def _prepare_move_line_default_vals(self):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        period_ids = self.env['tw.account.period']._get_current_periods()
        currency_id = self.company_id.currency_id.id
        branch_conf = self.company_id.branch_setting_id.account_setting_id

        line_vals_list = []       
        taxes = {}

         # * Set Debit account base on Assets or non Assets
        for record in self.move_asset_ids:
            subtotal = record.price_subtotal
            if record.type_assets == 'asset_prepayments':
                subtotal = record.price_total
                
            if record.is_cip:
                journal = branch_conf.journal_good_receive_cip_id
            elif record.type_assets == 'asset_prepayments':
                journal = branch_conf.journal_good_receive_prepaid_id
            else:
                journal = branch_conf.journal_good_receive_asset_id
                
            if not journal:
                raise Warning("Journal Good Receive untuk tipe aset ini belum disetting di Branch Config!")
            
            debit_account_id = journal.default_debit_account_id.id
            if not debit_account_id:
                raise Warning('Default debit account di %s belum ada' %(journal.name))
            
            credit_account_id = journal.default_credit_account_id.id
            if not credit_account_id:
                raise Warning('Default credit account di %s belum ada' %(journal.name))

            if not record.is_asset:
                if not record.product_id.categ_id.property_account_expense_categ_id:
                    raise Warning('Default Expense Account di %s belum ada' %(record.product_id.categ_id.name))
                debit_account_id = record.product_id.categ_id.property_account_expense_categ_id.id

            line_vals_list.append({
                'name': self.name,
                'date_maturity': self._get_default_date(),
                'amount_currency': subtotal,
                'currency_id': currency_id,
                'period_id': period_ids.id,
                'debit': subtotal,
                'credit': 0.0,
                'partner_id': self.partner_id.id,
                'account_id': debit_account_id,
                'company_id': self.company_id.id,
                'division': self.division,
            })
            if record.tax_ids:
                taxes[record.tax_ids] = taxes.get(record.tax_ids,0) + record.price_tax
        

            line_vals_list.append({
                    'name': record.product_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': credit_account_id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': 0.0,
                    'credit': subtotal,
                    'amount_currency': -subtotal,
                    'company_id': self.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
            })               
        
        return line_vals_list
    
    def _check_branch_config(self):
        branch_conf = self.company_id.branch_setting_id.account_setting_id
        if not branch_conf:
            raise Warning("Konfigurasi Branch Config Settlement belum dibuat !")
        else:
            if not branch_conf.journal_good_receive_asset_id:
                raise Warning("Konfigurasi Journal Good Receive Asset belum dibuat !")
    
    def _empty_tax_totals(self, currency):
        return {
            "currency_id": currency.id,
            "currency_pd": 0.0,
            "company_currency_id": currency.id,
            "company_currency_pd": 0.0,
            "has_tax_groups": False,
            "subtotals": [
                {
                    "tax_groups": [],
                    "tax_amount_currency": 0.0,
                    "tax_amount": 0.0,
                    "base_amount_currency": 0.0,
                    "base_amount": 0.0,
                    "name": "Untaxed Amount"
                }
            ],
            "base_amount_currency": 0.0,
            "base_amount": 0.0,
            "tax_amount_currency": 0.0,
            "tax_amount": 0.0,
            "same_tax_base": False,
            "total_amount_currency": 0.0,
            "total_amount": 0.0
        }

   

    