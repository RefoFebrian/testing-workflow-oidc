# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _, Command

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.float_utils import float_compare

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwAssetAcquisition(models.Model):
    """
    Model header untuk Akuisisi Asset.
    
    Flow:
    1. User pilih GR dan Line sebagai asset utama
    2. User bisa tambah kapitalisasi lines dari GR lain
    3. User isi tab pengguna dengan employee + serial number
    4. Confirm akan membuat asset sesuai jumlah pengguna
    5. Cancel akan cancel semua asset + reverse journal depresiasi
    """
    _name = "tw.asset.acquisition"
    _inherit = ["mail.thread", "mail.activity.mixin", "tw.attachment.mixin"]
    _description = "Asset Acquisition"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Reference',readonly=True,copy=False,default='New')
    date = fields.Date(string='Date', default=_get_default_date, required=True)
    note = fields.Text(string='Note')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options('Umum'), default='Umum')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Asset Configuration (dipindah dari GR)
    is_cip = fields.Boolean(related='asset_category_id.is_cip', string='Is CIP', store=True)
    is_final_cip = fields.Boolean('Is Final CIP?')

    # Amount Fields
    amount_base = fields.Float(string='Base Amount', compute='_compute_amounts', store=True, help="Nilai dari GR Line utama")
    amount_capitalization = fields.Float(string='Capitalization Amount', compute='_compute_amounts', store=True, help="Total nilai dari semua kapitalisasi lines")
    amount_total = fields.Float(string='Total Amount', compute='_compute_amounts', store=True, help="Base + Kapitalisasi")
    amount_per_unit = fields.Float(string='Amount per Unit', compute='_compute_amounts', store=True, help="Total Amount / Jumlah Pengguna")
    qty = fields.Integer(string='Quantity', default=1, required=True, help="Jumlah unit asset yang akan dibuat")
    asset_count = fields.Integer(compute='_compute_asset_count', string='Asset Count')

    # Audit Trail
    confirm_date = fields.Datetime('Confirmed on')
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    cancel_date = fields.Datetime('Cancelled on')
    cancel_uid = fields.Many2one('res.users', string='Cancelled by')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one(related='good_receive_id.partner_id', string='Vendor', store=True)
    
    # Main GR Reference
    good_receive_id = fields.Many2one(comodel_name='tw.good.receive', string='Good Receive', required=True, domain="[('company_id', '=', company_id), ('state', 'in', ['open', 'done']), ('move_asset_ids.is_acquired', '=', False)]")
    good_receive_line_id = fields.Many2one(comodel_name='tw.good.receive.asset.line', string='GR Line (Asset)', required=True, domain="[('picking_id', '=', good_receive_id), ('is_asset', '=', True), ('is_acquired', '=', False)]")
    product_id = fields.Many2one(related='good_receive_line_id.product_id', string='Product', store=True)
    description = fields.Char(related='good_receive_line_id.description', string='Description', readonly=True)
    
    # Asset Configuration
    asset_category_id = fields.Many2one(comodel_name='account.asset.category', string='Asset Category', required=True)
    asset_register_id = fields.Many2one(comodel_name='account.asset.asset', string='Asset (CIP)', domain="[('state', '=', 'CIP'), ('category_id.is_cip', '=', True)]", help="Pilih asset CIP jika ini adalah kapitalisasi ke CIP existing")
    employee_user_id = fields.Many2one(comodel_name='hr.employee', string='PIC Asset', help="Penanggung jawab asset (untuk semua unit)")

    # Lines
    capitalization_line_ids = fields.One2many(comodel_name='tw.asset.acquisition.line', inverse_name='acquisition_id', string='Kapitalisasi Lines')
    user_line_ids = fields.One2many(comodel_name='tw.asset.acquisition.user', inverse_name='acquisition_id', string='Pengguna Asset')

    # Same user for all units
    same_user_all = fields.Boolean(string='Pengguna Sama Semua?', default=False, help="Centang jika semua unit asset akan memiliki pengguna yang sama")
    same_user_employee_id = fields.Many2one(comodel_name='hr.employee', string='Pengguna', help="Pilih employee yang akan menjadi pengguna untuk semua unit")

    # Created Assets
    asset_ids = fields.One2many(comodel_name='account.asset.asset', inverse_name='acquisition_id', string='Created Assets', readonly=True)

    # Journal
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    move_line_ids = fields.One2many(related='move_id.line_ids', string='Journal Items', readonly=True)

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('good_receive_line_id', 'good_receive_line_id.price',
                 'capitalization_line_ids', 'capitalization_line_ids.price',
                 'qty')
    def _compute_amounts(self):
        """
        Calculate acquisition amounts based on per-unit prices.
        
        Base Amount = GR Line price per unit × Acquisition qty
        Capitalization Amount = sum of (cap line qty × cap line price per unit)
        Total Amount = Base + Capitalization
        Amount per Unit = Total / Acquisition qty (for creating individual assets)
        """
        for record in self:
            # Base amount = price per unit from GR Line × acquisition qty
            price_per_unit = record.good_receive_line_id.price if record.good_receive_line_id else 0.0
            acq_qty = record.qty or 1
            base = price_per_unit * acq_qty
            
            # Capitalization = sum of total prices from capitalization lines
            # Each capitalization line already has: price = qty × price_unit
            capitalization = sum(record.capitalization_line_ids.mapped('price'))
            
            total = base + capitalization
            
            record.amount_base = base
            record.amount_capitalization = capitalization
            record.amount_total = total
            record.amount_per_unit = total / acq_qty if acq_qty > 0 else total


    @api.depends('asset_ids')
    def _compute_asset_count(self):
        for record in self:
            record.asset_count = len(record.asset_ids)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Reset fields when company changes"""
        self.good_receive_id = False
        self.good_receive_line_id = False
        self.capitalization_line_ids = [(5, 0, 0)]
        self.user_line_ids = [(5, 0, 0)]

    @api.onchange('good_receive_id')
    def _onchange_good_receive_id(self):
        """Reset GR Line when GR changes"""
        self.good_receive_line_id = False

    @api.onchange('good_receive_line_id')
    def _onchange_good_receive_line_id(self):
        """
        Auto-fill asset category from product.
        Auto-fill CIP fields based on PO Header.
        """
        self.is_final_cip = False
        self.asset_register_id = False
        self.asset_category_id = False
        self.user_line_ids = False
        self.same_user_all = False
        self.same_user_employee_id = False
        if self.good_receive_line_id:
            product = self.good_receive_line_id.product_id
            if product and product.asset_category_id:
                self.asset_category_id = product.asset_category_id.id
            
            # Default qty to available qty
            self.qty = self.good_receive_line_id.qty_acquisition_available
            
            # === AUTO-DEFAULT CIP FIELDS FROM PO HEADER ===
            if self.asset_category_id and self.asset_category_id.is_cip:
                po_header = self.good_receive_line_id.purchase_order_id
                
                if po_header:
                    # 1. Auto-fill asset_register_id with CIP asset from same PO Header
                    gr_lines_same_po = self.env['tw.good.receive.asset.line'].search([
                        ('purchase_order_id', '=', po_header.id),
                        ('state', '!=', 'cancel'),
                    ])
                    
                    if gr_lines_same_po:
                        cip_asset = self.env['account.asset.asset'].search([
                            ('good_receive_line_ids', 'in', gr_lines_same_po.ids),
                            ('category_id.is_cip', '=', True),
                            ('state', '=', 'CIP'),
                        ], limit=1)
                        
                        if cip_asset:
                            self.asset_register_id = cip_asset.id
                            # Also auto-fill user_line_ids from CIP asset
                            cip_employee = cip_asset.employee_user_id
                            if cip_employee and self.qty > 0:
                                lines = []
                                for i in range(int(self.qty)):
                                    lines.append((0, 0, {
                                        'sequence': (i + 1) * 10,
                                        'employee_id': cip_employee.id,
                                        'serial_number': False,
                                    }))
                                self.user_line_ids = [(5, 0, 0)] + lines
                                self.same_user_all = True
                                self.same_user_employee_id = cip_employee.id
                    
                    # 2. Auto-check is_final_cip if this is last acquisition from PO
                    # Get all PO Lines with CIP category
                    po_lines_cip = po_header.order_line.filtered(
                        lambda l: l.product_id and l.product_id.asset_category_id and l.product_id.asset_category_id.is_cip
                    )
                    total_qty_po = sum(po_lines_cip.mapped('product_qty'))
                    
                    # Count qty already acquired from same PO (excluding current)
                    existing_acquisitions = self.search([
                        ('good_receive_line_id.purchase_order_id', '=', po_header.id),
                        ('state', '!=', 'cancel'),
                        ('is_cip', '=', True),
                    ])
                    # Exclude current record if editing
                    if self._origin and self._origin.id:
                        existing_acquisitions = existing_acquisitions.filtered(lambda a: a.id != self._origin.id)
                    
                    total_qty_acquired = sum(existing_acquisitions.mapped('qty'))
                    
                    # If this acquisition will complete all CIP items from PO
                    if total_qty_po > 0 and (total_qty_acquired + self.qty) >= total_qty_po:
                        self.is_final_cip = True
                    else:
                        self.is_final_cip = False

    @api.onchange('qty')
    def _onchange_qty(self):
        """Warn if qty exceeds available"""
        if self.good_receive_line_id and self.qty > self.good_receive_line_id.qty_acquisition_available:
            self.qty = self.good_receive_line_id.qty_acquisition_available
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Qty Acquisition (%d) melebihi Qty Available (%d) pada GR Line %s!") % (
                        self.qty, self.good_receive_line_id.qty_acquisition_available, self.good_receive_line_id.name)
                }
            }

    @api.onchange('asset_register_id')
    def _onchange_asset_register_id(self):
        """
        Auto-fill user_line_ids from selected CIP asset when doing kapitalisasi.
        Copy employee info from the CIP asset to new acquisition.
        """
        if self.asset_register_id and self.is_cip:
            # Get employee from CIP asset
            cip_employee = self.asset_register_id.employee_user_id
            if cip_employee and self.qty > 0:
                # Auto-fill user lines with same employee from CIP asset
                lines = []
                for i in range(int(self.qty)):
                    lines.append((0, 0, {
                        'sequence': (i + 1) * 10,
                        'employee_id': cip_employee.id,
                        'serial_number': False,
                    }))
                self.user_line_ids = [(5, 0, 0)] + lines
                self.same_user_all = True
                self.same_user_employee_id = cip_employee.id


    @api.onchange('same_user_all')
    def _onchange_same_user_all(self):
        """Clear user lines and same_user_employee_id when checkbox changes"""
        if not self.same_user_all:
            self.same_user_employee_id = False
        # Clear existing user lines when toggling
        self.user_line_ids = [(5, 0, 0)]

    @api.onchange('same_user_employee_id', 'qty')
    def _onchange_same_user_employee(self):
        """Auto-generate user lines when same_user_all is checked and employee is selected"""
        if self.same_user_all and self.same_user_employee_id and self.qty > 0:
            lines = []
            for i in range(int(self.qty)):
                lines.append((0, 0, {
                    'sequence': (i + 1) * 10,
                    'employee_id': self.same_user_employee_id.id,
                    'serial_number': False,
                }))
            self.user_line_ids = [(5, 0, 0)] + lines

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                company_id = vals.get('company_id', self.env.company.id)
                company = self.env['res.company'].browse(company_id)
                vals['name'] = self.env['ir.sequence'].get_sequence_code('AC', str(company.code)) or 'New'
        
        return super(TwAssetAcquisition, self).create(vals_list)
    
    # TODO: Delete if the transaction requires delete
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning(_('Warning! \nCannot delete records with a state other than draft!'))

        return super(TwAssetAcquisition, self).unlink()

    # 13: action methods
    def action_confirm(self):
        """
        Confirm akuisisi dan buat asset berdasarkan user_line_ids.
        Setiap user line akan menghasilkan 1 asset.
        """        
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman Asset Acquisition ini, karena state sudah {self._get_state_value()}')
        
        for record in self:
            # Validasi
            if not record.user_line_ids:
                raise Warning(_("Silahkan isi Tab Pengguna Asset terlebih dahulu!"))
            
            if len(record.user_line_ids) != record.qty:
                raise Warning(_("Jumlah pengguna (%d) harus sama dengan Quantity (%d)!") % (len(record.user_line_ids), record.qty))
            
            if not record.asset_category_id:
                raise Warning(_("Asset Category belum dipilih!"))
            
            # Validasi Qty Available
            if record.qty > record.good_receive_line_id.qty_acquisition_available:
                raise Warning(_("Qty Acquisition (%d) melebihi Qty Available (%d) pada GR Line %s!") % (
                    record.qty, record.good_receive_line_id.qty_acquisition_available, record.good_receive_line_id.name))

            # === CIP KAPITALISASI vs CIP PERTAMA ===
            if record.asset_register_id and record.is_cip:
                # CIP Kapitalisasi: TIDAK buat asset baru, hanya update value ke asset existing
                record._update_cip_asset()
            else:
                # CIP Pertama atau Non-CIP: Buat asset baru per user line
                for idx, user_line in enumerate(record.user_line_ids, start=1):
                    asset = record._create_asset_from_user_line(user_line, idx)
                    user_line.asset_id = asset.id
            
            # Update GR Line qty_acquired
            record.good_receive_line_id.qty_acquired += record.qty

            # Update Kapitalisasi GR Lines qty_acquired
            for line in record.capitalization_line_ids:
                if line.qty > line.good_receive_line_id.qty_acquisition_available:
                     raise Warning(_("Qty Kapitalisasi (%d) melebihi Qty Available (%d) pada GR Line %s!") % (
                        line.qty, line.good_receive_line_id.qty_acquisition_available, line.good_receive_line_id.name))
                line.good_receive_line_id.qty_acquired += line.qty
            
            # Create Acquisition Journal
            move = record._create_acquisition_journal()
            
            record.write({
                'state': 'done',
                'confirm_date': datetime.now(),
                'confirm_uid': self.env.user.id,
                'move_id': move.id if move else False
            })
        
        return True

    def action_done(self):
        """Set acquisition to done"""
        return self.write({'state': 'done'})

    def action_cancel(self):
        """
        Cancel akuisisi:
        1. Set semua asset ke state 'cancel'
        2. Reverse semua journal depresiasi
        3. Revert CIP value jika ini kapitalisasi ke CIP existing
        """
        for record in self:
            if record.state not in ['confirmed', 'done']:
                raise Warning(_("Hanya bisa cancel akuisisi yang sudah Confirmed atau Done!"))
            
            # Cancel all created assets
            for asset in record.asset_ids:
                # check assets, can't cancel Asset Acquisition if already depreciation on asset
                is_depreciation = asset.depreciation_line_ids.filtered(lambda depreciation: depreciation.move_check)
                if is_depreciation:
                    raise Warning(_(f'Asset {asset.name} sudah depresiasi, tidak bisa dilakukan Cancel!'))
                record._cancel_asset_and_reverse_journals(asset)

            # Revert CIP value jika ini kapitalisasi ke CIP existing
            if record.asset_register_id and record.is_cip:
                new_value = max(0.0, record.asset_register_id.value - record.amount_total)
                record.asset_register_id.write({'value': new_value})
                _logger.info("Acquisition %s cancelled - CIP %s value reduced by %s to %s", 
                             record.name, record.asset_register_id.name, record.amount_total, new_value)

            # Reverse Journal Akuisisi jika ada
            if record.move_id and record.move_id.state == 'posted':
                record.move_id._reverse_moves(
                    default_values_list=[{
                        'ref': _('Reversal of: %s - Acquisition Cancelled') % record.move_id.ref,
                        'date': fields.Date.today(),
                    }],
                    cancel=True
                )

            # Revert GR Line qty_acquired
            record.good_receive_line_id.qty_acquired = max(0.0, record.good_receive_line_id.qty_acquired - record.qty)

            # Revert Kapitalisasi GR Lines qty_acquired
            for line in record.capitalization_line_ids:
                line.good_receive_line_id.qty_acquired = max(0.0, line.good_receive_line_id.qty_acquired - line.qty)
            
            record.write({
                'state': 'cancel',
                'cancel_date': datetime.now(),
                'cancel_uid': self.env.user.id
            })
        
        return True

    def action_set_to_draft(self):
        """Reset to draft after cancel"""
        for record in self:
            if record.state != 'cancel':
                raise Warning(_("Hanya bisa reset ke draft dari status Cancel!"))
            
            record.write({'state': 'draft'})
        
        return True

    def action_view_assets(self):
        """Open asset list view"""
        self.ensure_one()
        return {
            'name': _('Assets'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.asset.asset',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.asset_ids.ids)],
            'context': {'create': False}
        }

    # 14: private methods
    def _create_acquisition_journal(self):
        self.ensure_one()
        if self.amount_total <= 0:
            return False
            
        branch_conf = self.company_id.branch_setting_id.account_setting_id
        journal = branch_conf.journal_acquisition_asset_id
        if not journal:
            raise Warning("Journal Akuisisi Asset belum disetting di Branch Config!")
            
        debit_account_id = self.asset_category_id.account_asset_id.id
        if not debit_account_id:
            raise Warning("Asset Account belum disetting pada Asset Category %s" % self.asset_category_id.name)
            
        move_line_vals = []
        
        # 1. Debit Asset Account for Total Amount
        move_line_vals.append({
            'name': self.name + ' - ' + (self.good_receive_line_id.product_id.name if self.good_receive_line_id else 'Capitalization'),
            'account_id': debit_account_id,
            'debit': self.amount_total,
            'credit': 0.0,
            'partner_id': self.partner_id.id,
            'division': self.division,
        })
        
        # 2. Credit Base GR Line
        if self.amount_base > 0 and self.good_receive_line_id:
            gr_line = self.good_receive_line_id
            account = self._get_clearing_account(branch_conf, gr_line)
                
            move_line_vals.append({
                'name': self.name + ' - Clearing GR ' + gr_line.picking_id.name,
                'account_id': account.id,
                'debit': 0.0,
                'credit': self.amount_base,
                'partner_id': self.partner_id.id,
                'division': self.division,
            })
            
        # 3. Credit Capitalization Lines
        for cap_line in self.capitalization_line_ids:
            if cap_line.price > 0 and cap_line.good_receive_line_id:
                gr_line = cap_line.good_receive_line_id
                account = self._get_clearing_account(branch_conf, gr_line)
                move_line_vals.append({
                    'name': self.name + ' - Clearing GR ' + gr_line.picking_id.name,
                    'account_id': account.id,
                    'debit': 0.0,
                    'credit': cap_line.price,
                    'partner_id': self.partner_id.id,
                    'division': self.division,
                })
                
        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'line_ids': [Command.create(vals) for vals in move_line_vals],
        }
        
        move = self.env['account.move'].create(move_vals)
        move.sudo().action_post()
        return move
    
    def _get_clearing_account(self, branch_conf, gr_line):
        if gr_line.is_asset:
            if gr_line.is_cip:
                j_gr = branch_conf.journal_good_receive_cip_id
            elif gr_line.type_assets == 'asset_prepayments':
                j_gr = branch_conf.journal_good_receive_prepaid_id
            else:
                j_gr = branch_conf.journal_good_receive_asset_id
            if not j_gr or not j_gr.default_debit_account_id:
                raise Warning("Journal GR / Default Debit Account belum disetting untuk produk %s" % gr_line.product_id.name)
            account = j_gr.default_debit_account_id
        else:
            account = gr_line.product_id.categ_id.property_account_expense_categ_id
        return account

    def _create_asset_from_user_line(self, user_line, idx):
        """
        Buat satu asset dari user line.
        
        :param user_line: tw.asset.acquisition.user record
        :param idx: index untuk naming
        :return: account.asset.asset record
        """
        self.ensure_one()
        
        product = self.product_id
        price_per_unit = self.amount_per_unit
        
        # Untuk prepaid asset, gunakan total termasuk tax
        if self.asset_category_id.type_assets == 'asset_prepayments':
            base_with_tax = self.good_receive_line_id.price_total if self.good_receive_line_id else 0.0
            cap_total = sum(self.capitalization_line_ids.mapped('price'))
            price_per_unit = (base_with_tax + cap_total) / (len(self.user_line_ids) or 1)
        
        # Asset name dengan suffix jika qty > 1
        asset_name = product.name
        if self.qty > 1:
            asset_name = f"{product.name} - {idx}"
        
        vals = {
            'name': asset_name,
            'code': self.asset_category_id.get_next_asset_code(),
            'category_id': self.asset_category_id.id,
            'value': price_per_unit,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.company_id.currency_id.id,
            'date': self.date,
            'purchase_date': self.good_receive_id.date,
            'product_id': product.id,
            'real_purchase_value': self.amount_total,
            'location_id': self.good_receive_id.location_dest_id.id,
            'employee_id': self.employee_user_id.id if self.employee_user_id else False,
            'employee_user_id': user_line.employee_id.id,
            'serial_number': user_line.serial_number or False,
            'first_depreciation_manual_date': self.date,
            'acquisition_id': self.id,
            'acquisition_line_id': user_line.id,
        }
        
        # Apply onchange values from category
        changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
        if changed_vals:
            vals.update(changed_vals.get('value', {}))
        
        # Link main GR Line for history (only base GR, not capitalization lines)
        vals['good_receive_line_ids'] = [(6, 0, [self.good_receive_line_id.id])]
        
        # Set state CIP sebelum create agar compute_depreciation_board di-skip
        if self.is_cip and not self.is_final_cip:
            vals['state'] = 'CIP'

        # Create asset
        asset = self.env['account.asset.asset'].create(vals)
        
        # Update depreciation end date (hanya jika bukan CIP)
        if asset.state != 'CIP' and asset.depreciation_line_ids:
            last_date_depreciation = asset.depreciation_line_ids[-1].depreciation_date
            asset.method_end = last_date_depreciation
        
        # Set note for prepaid
        if asset.type_assets == 'asset_prepayments':
            asset.note = self.good_receive_line_id.description
        
        # Validate non-CIP asset
        if not self.is_cip or self.is_final_cip:
            asset.validate()
        
        return asset

    def _update_cip_asset(self):
        """
        Update existing CIP asset dengan kapitalisasi.
        Digunakan jika asset_register_id dipilih (CIP existing).
        """
        self.ensure_one()
        
        if not self.asset_register_id:
            return
        
        # Add capitalization value to CIP
        new_value = self.asset_register_id.value + self.amount_total
        self.asset_register_id.write({
            'value': new_value,
            'state': 'CIP'
        })
        
        # If final CIP, change category and validate
        if self.is_final_cip:
            self.asset_register_id.write({
                'category_id': self.asset_category_id.id
            })
            self.asset_register_id.validate()

    def _cancel_asset_and_reverse_journals(self, asset):
        """
        Cancel asset dan reverse semua journal depresiasi.
        
        :param asset: account.asset.asset record
        """
        # Get all posted depreciation moves
        depreciation_moves = asset.depreciation_line_ids.filtered(
            lambda l: l.move_id and l.move_id.state == 'posted'
        ).mapped('move_id')
        
        # Reverse all depreciation moves
        for move in depreciation_moves:
            # Create reverse entry
            reverse_move = move._reverse_moves(
                default_values_list=[{
                    'ref': _('Reversal of: %s - Acquisition Cancelled') % move.ref,
                    'date': fields.Date.today(),
                }],
                cancel=True
            )
            _logger.info("Reversed depreciation journal %s for asset %s", move.name, asset.name)
        
        # Set asset to cancel state
        asset.write({'state': 'cancel'})
        
        _logger.info("Asset %s cancelled due to acquisition cancellation", asset.name)
