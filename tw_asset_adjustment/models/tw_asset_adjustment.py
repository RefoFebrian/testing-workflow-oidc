# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAssetAdjustment(models.Model):
    _name = "tw.asset.adjustment"
    _description = 'Asset Adjustment'
    _order = 'date desc'
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today()
        
    # 8: fields
    name = fields.Char(string='Name',compute='_compute_name',store=True)
    date = fields.Date(string='Date',default=_get_default_date)
    number_depreciation = fields.Integer(string='Number of Depreciations')
    new_number_depreciation = fields.Integer(string='New Number of Depreciations')
    purchase_value = fields.Float(string='Gross Value')
    new_purchase_value = fields.Float(string='New Gross Value')
    state = fields.Selection([
        ('draft','Draft'),  
        ('post','Posted')],default='draft',string='State')
    
    bool_journal_category = fields.Boolean(string='Create Journal Category',default=True)
    bool_journal_gross_value = fields.Boolean(string='Create Journal Gross Value',default=True)
    division = fields.Selection([('Umum','Umum')],string='Division',default='Umum')
    bool_journal_branch = fields.Boolean(string='Create Journal Branch',default=True)
    purchase_date = fields.Date(string='Effective Date')
    new_purchase_date = fields.Date(string='New Effective Date')
    
    # Kapitalisasi fields
    amount_capitalization = fields.Float(string='Total Kapitalisasi', compute='_compute_capitalization_amount', store=True)
    base_gross_value = fields.Float(string='Base Gross Value', help="Nilai dasar sebelum kapitalisasi. Diisi dari purchase_value atau manual input user.")
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Posted by")
    confirm_date = fields.Datetime('Posted on')
    
    # 9: relation fields
    company_id = fields.Many2one('res.company',string='Branch',default=lambda self: self.env.company)
    new_company_id = fields.Many2one('res.company',string='New Branch')
    asset_id = fields.Many2one('account.asset.asset',string='Asset No')
    product_id = fields.Many2one(related="asset_id.product_id")
    category_id = fields.Many2one('account.asset.category',string='Category')
    new_category_id = fields.Many2one('account.asset.category',string='New Category')
    move_id = fields.Many2one('account.move', string='Account Entry', copy=False)
    move_ids = fields.One2many('account.move.line',related='move_id.line_ids',string='Journal Items', readonly=True)   
    acquisition_move_id = fields.Many2one('account.move', string='Journal Akuisisi Entry', copy=False)
    acquisition_move_ids = fields.One2many('account.move.line',related='acquisition_move_id.line_ids',string='Journal Akuisisi Items', readonly=True)   
    employee_user_id = fields.Many2one("hr.employee",string="Pengguna Asset")
    new_employee_user_id = fields.Many2one("hr.employee",string="New Pengguna Asset")

    # Kapitalisasi fields
    capitalization_line_ids = fields.One2many('tw.asset.adjustment.line', 'adjustment_id', string='Kapitalisasi Lines')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for item in self:
            item.name = self.env['ir.sequence'].get_sequence_code('AA', str(item.company_id.code))

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.asset_id = False
    

    @api.onchange('asset_id')
    def onchange_asset(self):
        self.category_id = False
        self.new_category_id = False
        self.number_depreciation = False
        self.new_number_depreciation = False
        self.purchase_value = False
        self.new_purchase_value = False
        self.base_gross_value = False
        self.company_id = False
        self.new_company_id = False
        self.purchase_date = False
        self.new_purchase_date = False
        if self.asset_id:
            self.category_id = self.asset_id.category_id.id
            self.new_category_id = self.asset_id.category_id.id
            self.number_depreciation = self.asset_id.method_number
            self.new_number_depreciation = self.asset_id.method_number
            self.purchase_value = self.asset_id.value
            self.new_purchase_value = self.asset_id.value
            self.base_gross_value = self.asset_id.value  # Default base = asset value
            self.company_id = self.asset_id.company_id.id
            self.new_company_id = self.asset_id.company_id.id
            self.purchase_date = self.asset_id.purchase_date
            self.new_purchase_date = self.asset_id.purchase_date
            self.employee_user_id = self.asset_id.employee_user_id.id
            self.new_employee_user_id = self.asset_id.employee_user_id.id

    @api.onchange('new_category_id')
    def onchange_new_category(self):
        self.new_number_depreciation = False
        if self.new_category_id :
            self.new_number_depreciation = self.new_category_id.method_number

    @api.depends('capitalization_line_ids.price')
    def _compute_capitalization_amount(self):
        for record in self:
            record.amount_capitalization = sum(line.price for line in record.capitalization_line_ids)

    @api.onchange('capitalization_line_ids')
    def _onchange_capitalization_lines(self):
        """
        Auto-update new_purchase_value = base_gross_value + total kapitalisasi
        """
        total_cap = sum(line.price for line in self.capitalization_line_ids)
        # Gunakan base_gross_value jika sudah di-set, otherwise purchase_value
        base = self.base_gross_value or self.purchase_value or 0
        self.new_purchase_value = base + total_cap

    @api.onchange('new_purchase_value')
    def _onchange_new_purchase_value(self):
        """
        Saat user ubah New Gross Value secara manual,
        update base_gross_value = new_purchase_value - kapitalisasi
        """
        total_cap = sum(line.price for line in self.capitalization_line_ids)
        # Calculate base value dari input user
        self.base_gross_value = (self.new_purchase_value or 0) - total_cap
    
    def _compute_catchup_depreciation(self):
        """
        Compute catch-up depreciation amount when asset value is adjusted.
        
        Catch-up = periods_posted × (new_monthly_depr - old_monthly_depr)
        
        Example:
        - Original: Value 12,000,000, 60 months → 200,000/month
        - After 12 months posted → 2,400,000 depreciated
        - Adjustment: Value → 18,000,000
        - New monthly: 18,000,000 / 60 = 300,000
        - Catch-up: 12 × (300,000 - 200,000) = 1,200,000
        - First unposted line: 300,000 + 1,200,000 = 1,500,000
        """
        self.ensure_one()
        asset = self.asset_id
        
        if not asset or asset.state != 'open':
            return 0.0
        
        # Get posted depreciation lines count
        posted_lines = asset.depreciation_line_ids.filtered(lambda l: l.move_check)
        if not posted_lines:
            return 0.0  # No catch-up needed if nothing posted yet
        
        periods_posted = len(posted_lines)
        method_number = self.new_number_depreciation or asset.method_number
        salvage_value = asset.salvage_value or 0.0
        
        # Calculate old and new monthly depreciation (linear method)
        old_monthly = (self.purchase_value - salvage_value) / method_number if method_number else 0
        new_monthly = (self.new_purchase_value - salvage_value) / method_number if method_number else 0
        
        # Catch-up = periods_posted × difference
        catchup_amount = periods_posted * (new_monthly - old_monthly)
        
        return catchup_amount

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('asset_id'):
                asset = self.env['account.asset.asset'].browse(vals['asset_id'])
                vals.update({
                    'category_id': asset.category_id.id,
                    'number_depreciation': asset.method_number,
                    'purchase_value': asset.value,
                    'purchase_date': asset.purchase_date,
                    'company_id': asset.company_id.id,
                })
        return super(TwAssetAdjustment,self).create(vals_list)
    
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning("Adjustment Asset %s tidak bisa dihapus dalam status 'Posted' !" %(item.name))
        return super(TwAssetAdjustment, self).unlink()         

    # 14: private methods
    def _validate_capitalization_lines(self):
        """
        Validasi kapitalisasi lines sebelum action:
        1. Cek qty tidak melebihi qty_acquisition_available
        2. Cek GR Line tidak digunakan di adjustment lain yang belum posted
        """
        self.ensure_one()
        for line in self.capitalization_line_ids:
            # Validasi qty
            if line.qty > line.good_receive_line_id.qty_acquisition_available:
                raise Warning(_("Qty Kapitalisasi (%d) melebihi Qty Available (%d) pada GR Line %s!") % (
                    line.qty, line.good_receive_line_id.qty_acquisition_available, line.good_receive_line_id.name))
            
            # Cek duplikasi di adjustment lain (selain yg sudah posted)
            existing_lines = self.env['tw.asset.adjustment.line'].search([
                ('good_receive_line_id', '=', line.good_receive_line_id.id),
                ('id', '!=', line.id),
                ('adjustment_id', '!=', self.id),
                ('adjustment_id.state', '!=', 'post'),
            ])
            if existing_lines:
                adjustment_names = existing_lines.mapped('adjustment_id.name')
                raise Warning(_("GR Line %s sudah digunakan di Adjustment lain:\n%s\n\nPastikan tidak terjadi duplikasi kapitalisasi!") % (
                    line.good_receive_line_id.display_name or line.good_receive_line_id.product_id.name,
                    ', '.join(adjustment_names)
                ))

    def post_adjustment(self):
        self.ensure_one()
        if self.state == 'post':
            raise Warning("Adjustment Asset %s sudah dalam status 'Posted'!" % (self.name))

        # Validasi kapitalisasi lines
        self.sudo()._validate_capitalization_lines()

        asset_update_vals = {}
        if self.new_category_id and self.new_category_id != self.category_id:
            asset_update_vals['category_id'] = self.new_category_id.id
        if self.new_purchase_value and self.new_purchase_value != self.purchase_value:
            asset_update_vals['value'] = self.new_purchase_value
        if self.new_number_depreciation and self.new_number_depreciation != self.number_depreciation:
            asset_update_vals['method_number'] = self.new_number_depreciation
        if self.new_company_id and self.new_company_id != self.company_id:
            asset_update_vals['company_id'] = self.new_company_id.id
        if self.new_purchase_date and self.new_purchase_date != self.purchase_date:
            asset_update_vals['purchase_date'] = self.new_purchase_date
            asset_update_vals['date'] = self.new_purchase_date
            asset_update_vals['first_depreciation_manual_date'] = self.new_purchase_date
        if self.new_employee_user_id and self.new_employee_user_id != self.employee_user_id:
            asset_update_vals['employee_user_id'] = self.new_employee_user_id.id

        move = self.sudo()._create_account_move()
        
        acquisition_move = False
        if self.capitalization_line_ids:
            acquisition_move = self.sudo()._create_acquisition_journal()

        adjustment_write_vals = {
            'state': 'post',
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now(),
        }
        if move:
            adjustment_write_vals['move_id'] = move.id
            
        if acquisition_move:
            adjustment_write_vals['acquisition_move_id'] = acquisition_move.id

        if asset_update_vals:
            # Calculate catch-up depreciation BEFORE updating asset value
            if 'value' in asset_update_vals:
                catchup_amount = self._compute_catchup_depreciation()
                if catchup_amount:
                    # Set catch-up amount on asset - will be used by compute_depreciation_board
                    asset_update_vals['catchup_depreciation_amount'] = catchup_amount
            
            asset = self.asset_id.sudo()
            asset.write(asset_update_vals)
            if asset.depreciation_line_ids:
                last_date_depreciation = asset.depreciation_line_ids[-1].depreciation_date
                asset.method_end = last_date_depreciation
            asset.compute_depreciation_board()

        # Update qty_acquired di GR Lines
        for line in self.capitalization_line_ids:
            line.good_receive_line_id.sudo().qty_acquired += line.qty

        self.sudo().write(adjustment_write_vals)
        return True

    def _create_account_move(self):
        self.ensure_one()
        
        line_vals_list = self._prepare_move_line_vals()
        if not line_vals_list:
            return False

        branch_config = self.company_id.branch_setting_id.account_setting_id
        if not branch_config:
            raise Warning("Branch Config tidak ditemukan!")
        journal = branch_config.journal_asset_adjustment_id
        if not journal:
            raise Warning("Journal Asset Adjustment belum diisi dalam master Branch Config!")

        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'division': self.division,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'line_ids': [Command.create(vals) for vals in line_vals_list],
        }
        
        move = self.env['account.move'].create(move_vals)
        move.sudo().action_post()
        return move

    def _create_acquisition_journal(self):
        self.ensure_one()
        if not self.capitalization_line_ids:
            return False
            
        branch_conf = self.company_id.branch_setting_id.account_setting_id
        journal = branch_conf.journal_acquisition_asset_id
        if not journal:
            raise Warning("Journal Akuisisi Asset belum disetting di Branch Config!")
            
        debit_account_id = self.new_category_id.account_asset_id.id
        if not debit_account_id:
            raise Warning("Asset Account belum disetting pada Asset Category %s" % self.new_category_id.name)
            
        capitalization_amount = sum(line.price for line in self.capitalization_line_ids)
        if capitalization_amount < 0.0001:
            return False

        move_line_vals = []
        
        # 1. Debit Asset Account for Total Capitalization Amount
        move_line_vals.append({
            'name': self.asset_id.name + ' (Capitalization via GR)',
            'account_id': debit_account_id,
            'debit': capitalization_amount,
            'credit': 0.0,
            'partner_id': self.asset_id.partner_id.id,
            'division': self.division,
        })
        
        # 2. Credit Capitalization GR Lines (clearing)
        for cap_line in self.capitalization_line_ids:
            if cap_line.price > 0 and cap_line.good_receive_line_id:
                gr_line = cap_line.good_receive_line_id
                account = self.env['tw.asset.acquisition']._get_clearing_account(branch_conf, gr_line)    
                move_line_vals.append({
                    'name': self.asset_id.name + ' - Clearing GR ' + gr_line.picking_id.name,
                    'account_id': account.id,
                    'debit': 0.0,
                    'credit': cap_line.price,
                    'partner_id': self.asset_id.partner_id.id,
                    'division': self.division,
                })
                
        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'partner_id': self.asset_id.partner_id.id,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'line_ids': [Command.create(vals) for vals in move_line_vals],
        }
        
        move = self.env['account.move'].create(move_vals)
        move.sudo().action_post()
        return move

    def _prepare_move_line_vals(self):
        self.ensure_one()
        line_vals_list = []
        
        nilai_perolehan = self.asset_id.value
        nilai_akumulasi = self.asset_id.value - self.asset_id.value_residual
        line_name = self.asset_id.product_id.name if self.asset_id.product_id else self.asset_id.name

        if self.bool_journal_category and self.new_category_id != self.category_id:
            old_asset_acc = self.category_id.account_asset_id
            new_asset_acc = self.new_category_id.account_asset_id
            old_dep_acc = self.category_id.account_depreciation_id
            new_dep_acc = self.new_category_id.account_depreciation_id
            
            if not all([old_asset_acc, new_asset_acc, old_dep_acc, new_dep_acc]):
                raise Warning("Lengkapi Akun Aset dan Akun Akumulasi Depresiasi di Kategori Aset lama dan baru!")

            line_vals_list.extend([
                {'name': line_name + ' (New Category)', 'division': self.division, 'account_id': new_asset_acc.id, 'debit': nilai_perolehan, 'credit': 0.0},
                {'name': line_name + ' (Old Category)', 'division': self.division, 'account_id': old_asset_acc.id, 'debit': 0.0, 'credit': nilai_perolehan}
            ])

            if nilai_akumulasi > 0:
                line_vals_list.extend([
                    {'name': line_name + ' (Depreciation Old Category)', 'division': self.division, 'account_id': old_dep_acc.id, 'debit': nilai_akumulasi, 'credit': 0.0},
                    {'name': line_name + ' (Depreciation New Category)', 'division': self.division, 'account_id': new_dep_acc.id, 'debit': 0.0, 'credit': nilai_akumulasi}
                ])

        if self.bool_journal_gross_value and self.new_purchase_value != self.purchase_value:
            value_change = self.new_purchase_value - self.purchase_value
            asset_account_id = self.new_category_id.account_asset_id.id
            
            branch_config = self.company_id.branch_setting_id.account_setting_id
            journal = branch_config.journal_asset_adjustment_id
            
            # Jika ada kapitalisasi dari GR, kita tidak catat di jurnal Adjustment ini.
            # Jurnal kapitalisasinya diurus terpisah di _create_acquisition_journal.
            if self.capitalization_line_ids:
                capitalization_amount = sum(line.price for line in self.capitalization_line_ids)
                
                # Handle sisa difference jika ada adjustment manual juga
                remaining_diff = value_change - capitalization_amount
                if remaining_diff != 0:
                    if remaining_diff > 0:
                        adj_acc = journal.default_debit_account_id.id or journal.default_credit_account_id.id
                        line_vals_list.extend([
                            {'name': line_name + ' (Gross Value Add)', 'division': self.division, 'account_id': asset_account_id, 'debit': remaining_diff, 'credit': 0.0},
                            {'name': line_name + ' (Gross Value Adj)', 'division': self.division, 'account_id': adj_acc, 'debit': 0.0, 'credit': remaining_diff}
                        ])
                    else:
                        adj_acc = journal.default_credit_account_id.id or journal.default_debit_account_id.id
                        line_vals_list.extend([
                            {'name': line_name + ' (Gross Value Reduce)', 'division': self.division, 'account_id': asset_account_id, 'debit': 0.0, 'credit': -remaining_diff},
                            {'name': line_name + ' (Gross Value Adj)', 'division': self.division, 'account_id': adj_acc, 'debit': -remaining_diff, 'credit': 0.0}
                        ])
            else:
                # Logic lama untuk adjustment manual
                if value_change > 0:
                    adjustment_account_id = journal.default_debit_account_id.id if journal.default_debit_account_id else journal.default_credit_account_id.id
                else:
                    adjustment_account_id = journal.default_credit_account_id.id if journal.default_credit_account_id else journal.default_debit_account_id.id
                if not adjustment_account_id:
                    raise Warning("Lengkapi Default Debit & Credit Account di Journal Penyesuaian Aset!")

                line_vals_list.extend([
                    {'name': line_name + ' (Gross Value New)', 'division': self.division, 'account_id': asset_account_id, 'debit': value_change if value_change > 0 else 0.0, 'credit': -value_change if value_change < 0 else 0.0},
                    {'name': line_name + ' (Gross Value Adjustment)', 'division': self.division, 'account_id': adjustment_account_id, 'debit': -value_change if value_change < 0 else 0.0, 'credit': value_change if value_change > 0 else 0.0}
                ])
            
        if self.bool_journal_branch and self.new_company_id != self.company_id:
            asset_acc = self.new_category_id.account_asset_id.id
            dep_acc = self.new_category_id.account_depreciation_id.id

            line_vals_list.extend([
                {'name': line_name + ' (Branch New)', 'division': self.division, 'account_id': asset_acc, 'debit': nilai_perolehan, 'credit': 0.0, 'company_id': self.new_company_id.id},
                {'name': line_name + ' (Branch Old)', 'division': self.division, 'account_id': asset_acc, 'debit': 0.0, 'credit': nilai_perolehan, 'company_id': self.company_id.id}
            ])

            if nilai_akumulasi > 0:
                 line_vals_list.extend([
                    {'name': line_name, 'division': self.division, 'account_id': dep_acc, 'debit': nilai_akumulasi, 'credit': 0.0, 'company_id': self.company_id.id},
                    {'name': line_name, 'division': self.division, 'account_id': dep_acc, 'debit': 0.0, 'credit': nilai_akumulasi, 'company_id': self.new_company_id.id}
                ])

        final_list = []
        for line in line_vals_list:
            if abs(line.get('debit', 0.0)) < 0.0001 and abs(line.get('credit', 0.0)) < 0.0001:
                continue
            line.setdefault('partner_id', self.asset_id.partner_id.id)
            line.setdefault('ref', self.name)
            line.setdefault('division', self.division)
            final_list.append(line)
            
        return final_list