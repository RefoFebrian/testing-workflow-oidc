# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from lxml import etree

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.osv import expression
from odoo.tools import float_is_zero

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class TwAccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    # 8: fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    state = fields.Selection(selection_add=[
        ('CIP', 'CIP'),
        ('cancel', 'Cancelled')
    ], ondelete={
        'CIP': 'set default',
        'cancel': 'set default'
    })
    code = fields.Char(string='Code')
    
    purchase_date = fields.Date(string='Purchase Date')
    real_purchase_value = fields.Float(string='Real Purchase Value')
    type_assets = fields.Selection(related='category_id.type_assets', string='Categ Type', readonly=True, store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options('Umum'))

    # Field to store catch-up amount during adjustment
    catchup_depreciation_amount = fields.Monetary(
        string='Catch-up Depreciation',
        default=0.0,
        help='Temporary field to store catch-up depreciation amount during adjustment.'
    )
    
    # 9: relation fields
    product_id = fields.Many2one("product.product",domain=[('purchase_ok', '=', True),('categ_id', 'ilike', 'Non-trade')], string="Product")
    employee_id = fields.Many2one("hr.employee", string="Penanggung Jawab")
    employee_user_id = fields.Many2one("hr.employee",string="Pengguna Asset")
    acquisition_id = fields.Many2one("tw.asset.acquisition", string="Acquisition Reference", readonly=True)
    acquisition_line_id = fields.Many2one("tw.asset.acquisition.user", string="Acquisition User Line", readonly=True)
    serial_number = fields.Char(string="Engine No", help="Nomor serial unit asset")
    location_id = fields.Many2one("stock.location", string="Lokasi", domain=[('type_id.value','=','asset')])
    history_employee_user_ids = fields.One2many(comodel_name="tw.asset.user.history", inverse_name="asset_id")
    good_receive_line_ids = fields.Many2many(
        comodel_name="tw.good.receive.asset.line",
        relation='account_asset_good_receive_line_rel', # Nama tabel relasi di database
        column1='asset_id',
        column2='gr_line_id',
        string='Good Receive History'
    )
    # 10: fields with default value
    
    # 11: compute and search fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    def compute_depreciation_board(self):
        """
        Override to handle catch-up depreciation mechanism.
        When catchup_depreciation_amount is set, use constant monthly rate based on 
        new_value / total_method_number instead of residual / remaining_periods.
        WHY OVERRIDE?
        =============
        Odoo Standard: menghitung depresiasi = residual_value / remaining_periods
        Catch-up Mode: menghitung depresiasi = new_value / total_periods (rate konstan)
        
        EXAMPLE:
        --------
        Asset: 40,000,000 | 60 bulan | Monthly: 666,666.67
        Posted: 4 bulan (2,666,666.67)
        
        Adjustment: Value → 50,000,000
        
        ODOO STANDARD:
          - Residual: 50M - 2.67M = 47.33M
          - Remaining: 60 - 4 = 56 bulan
          - Monthly: 47.33M / 56 = 845,238.10  ❌ (rate berubah)
        
        CATCH-UP MODE (Custom):
          - New Monthly: 50M / 60 = 833,333.33 ✅ (rate konstan)
          - Selisih: 833,333 - 666,667 = 166,667
          - Catch-up: 4 × 166,667 = 666,667
          - Line 1: 833,333 + 666,667 = 1,500,000 ✅
          - Line 2+: 833,333.33 ✅
        
        CIP assets are skipped — depreciation only runs after asset is validated.
        """
        self.ensure_one()

        # CIP tidak perlu compute depreciation board
        if self.state == 'CIP':
            return True

        posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        # Get catch-up amount if set
        catchup_amount = self.catchup_depreciation_amount or 0.0
        use_catchup_mode = catchup_amount != 0.0

        if self.value_residual != 0.0:
            # If catch-up mode: use constant monthly rate = value / method_number
            # Otherwise: use standard Odoo calculation
            if use_catchup_mode:
                # Catch-up mode: constant monthly rate
                monthly_amount = (self.value - self.salvage_value) / self.method_number if self.method_number else 0
                amount_to_depr = monthly_amount * (self.method_number - len(posted_depreciation_line_ids))
                residual_amount = amount_to_depr
            else:
                amount_to_depr = residual_amount = self.value_residual

            # Calculate depreciation date
            if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                last_depreciation_date = fields.Date.from_string(posted_depreciation_line_ids[-1].depreciation_date)
                depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
            else:
                depreciation_date = self.date
                if self.date_first_depreciation == 'last_day_period':
                    depreciation_date = depreciation_date + relativedelta(day=31)
                    if self.method_period == 12:
                        depreciation_date = depreciation_date + relativedelta(month=int(self.company_id.fiscalyear_last_month))
                        depreciation_date = depreciation_date + relativedelta(day=int(self.company_id.fiscalyear_last_day))
                        if depreciation_date < self.date:
                            depreciation_date = depreciation_date + relativedelta(years=1)
                elif self.first_depreciation_manual_date and self.first_depreciation_manual_date != self.date:
                    depreciation_date = self.first_depreciation_manual_date

            total_days = (depreciation_date.year % 4) and 365 or 366
            month_day = depreciation_date.day
            undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)

            # Linear method: selalu gunakan method_number sebagai jumlah line
            # Prorata menambah +1 di parent, tapi custom linear Teto pakai rate konstan
            # sehingga tidak perlu extra line untuk prorata
            if self.method == 'linear':
                undone_dotation_number = self.method_number
            
            is_first_unposted = True

            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                sequence = x + 1
                
                if use_catchup_mode:
                    # Use constant monthly amount
                    if sequence == undone_dotation_number:
                        # Last line: use remaining
                        amount = residual_amount
                    else:
                        amount = monthly_amount
                else:
                    amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr,
                                                        undone_dotation_number, posted_depreciation_line_ids,
                                                        total_days, depreciation_date)
                
                amount = self.currency_id.round(amount)
                
                # Add catch-up to first unposted line only
                if is_first_unposted and catchup_amount != 0:
                    amount += catchup_amount
                    amount = self.currency_id.round(amount)
                    is_first_unposted = False
                
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                    
                residual_amount -= (amount - catchup_amount if is_first_unposted == False and x == len(posted_depreciation_line_ids) else amount)
                if x == len(posted_depreciation_line_ids) and catchup_amount:
                    residual_amount = amount_to_depr - monthly_amount  # Reset after first line
                    
                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': (self.code or '') + '/' + str(sequence),
                    'remaining_value': max(0, residual_amount),
                    'depreciated_value': self.value - (self.salvage_value + max(0, residual_amount)),
                    'depreciation_date': depreciation_date,
                }
                commands.append((0, False, vals))

                depreciation_date = depreciation_date + relativedelta(months=+self.method_period)

                if month_day > 28 and self.date_first_depreciation == 'manual':
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=min(max_day_in_month, month_day))

                if not self.prorata and self.method_period % 12 != 0 and self.date_first_depreciation == 'last_day_period':
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)

        # Reset catch-up amount after applying
        write_vals = {'depreciation_line_ids': commands}
        if catchup_amount != 0:
            write_vals['catchup_depreciation_amount'] = 0.0
        self.write(write_vals)

        return True
    
    @api.depends('name','product_id')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            
            if record.code:
                name = record.code + ' - ' + record.name
            
            if record.product_id:
                name = f"[{name}] {record.product_id.name} "
            record.display_name = name

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        prepaid_type = self._context.get('default_prepaid_type',False)
        for vals in vals_list:
            if vals.get('company_id'):
                company = self.env['res.company'].browse(vals['company_id'])
                if prepaid_type:
                    vals['name'] = self.env['ir.sequence'].get_sequence_code('PREPAID', str(company.code))
                else:
                    vals['name'] = self.env['ir.sequence'].get_sequence_code('REGAS', str(company.code))
            
        employees_to_track = [vals.get('employee_user_id') for vals in vals_list if vals.get('employee_user_id')]
        
        assets = super().create(vals_list)
        # Panggil history creator jika ada pengguna baru
        for employee_id in employees_to_track:
            if employee_id:
                assets.create_history_employee_user(employee_id=employee_id, transaction_name='Asset Creation')

        return assets
    
    def write(self, vals):
        # check perubahan employee_user_id sebelum write
        if 'employee_user_id' in vals and vals['employee_user_id'] != self.employee_user_id.id:
            # Jika pengguna baru diisi, buat history
            if vals['employee_user_id']:
                self.create_history_employee_user(
                    employee_id=vals['employee_user_id'], 
                    transaction_name='Manual Update'
                )
            # Jika pengguna dikosongkan, buat history 'Pengosongan'
            else:
                self.create_history_employee_user(
                    employee_id=False, 
                    transaction_name='User Removal'
                )
        
        return super().write(vals)
    
    def get_formview_action(self, access_uid=None):
        """ Override this method to add access control for user form view """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_asset_management.group_tw_account_asset_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        domain = args or []
        match_domain = []
        if name:
            match_domain = ['|',('name', operator, name), ('product_id.name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                match_domain = ['&', '!'] + match_domain[1:]
        
        assets = self.search_fetch(expression.AND([domain, match_domain]), ['name'], limit=limit)
        return [(asset.id, f"[{asset.name}] {asset.product_id.name} ") for asset in assets.sudo()]

  
    # 13: action methods
    def action_prepaid_asset_view(self):
        domain = [('type_assets', '=', 'asset_prepayments')]
        list_view = self.env.ref('tw_asset_management.view_account_asset_prepaid_tree')
        form_view = self.env.ref('tw_asset_management.view_account_asset_asset_prepaid_form')
        # search_view = self.env.ref('tw_asset_management.tw_inherit_purchase_order_asset_search_view')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prepaid Asset',
            'path': 'prepaid-asset',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.asset',
            'target': 'current',
            'domain': domain,
            'views': [(list_view.id, 'list'), (form_view.id, 'form')],
            # 'search_view_id': search_view.id,
            'context': {
                'default_asset_type': 'purchase',
                'prepaid_type': 'prepaid',
                'search_default_category_id': False,
                'default_state': 'draft',
                'default_company_id': self.company_id.id
            },
        }
   
    def action_fixed_asset_view(self):
        domain = [('type_assets', '!=', 'asset_prepayments')]
        list_view = self.env.ref('tw_asset_management.tw_inherit_account_asset_asset_purchase_list_view')
        form_view = self.env.ref('tw_asset_management.tw_inherit_account_asset_asset_form_view')
        # search_view = self.env.ref('tw_asset_management.tw_inherit_purchase_order_asset_search_view')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asset',
            'path': 'fixed-asset',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.asset',
            'target': 'current',
            'domain': domain,
            'views': [(list_view.id, 'list'), (form_view.id, 'form')],
            # 'search_view_id': search_view.id,
            'context': {
                'default_asset_type': 'purchase',
                'search_default_category_id': False,
                'default_state': 'draft',
                'default_company_id': self.company_id.id
            },
        }
    
    def action_generate_depreciation_entries(self):
        if self.state != 'open':
            raise Warning(_('Asset must be in open state to compute depreciation entries'))
        date = fields.Date.today()
        depreciation_ids = self.env['account.asset.depreciation.line'].search([
            ('asset_id', 'in', self.ids), 
            ('depreciation_date', '<=', date),
            ('move_check', '=', False)])
        return depreciation_ids.create_move()
    
    def validate(self):
        """Override validate to add prepaid validation and compute depreciation for CIP assets."""
        # Track CIP assets sebelum validate (state akan berubah ke 'open')
        cip_assets = self.filtered(lambda a: a.state == 'CIP')
        for asset in self:
            if asset.type_assets == 'asset_prepayments' and not asset.note:
                raise Warning(_('Note field is required for Prepaid assets'))
            if not asset.code:
                code = asset.category_id.asset_code
                if not code:
                    raise Warning("Silahkan input Asset Code pada Asset Categories !")
                asset.code = self.env['ir.sequence'].get_sequence_code_only(code)

        result = super(TwAccountAssetAsset, self).validate()

        # CIP → Open: compute depreciation board yang di-skip saat create
        for asset in cip_assets:
            asset.compute_depreciation_board()

        return result
    # 14: private methods
    def create_history_employee_user(self, employee_id=None, transaction_name=''):
        """Membuat record history pengguna asset."""
        
        # Tentukan ID pengguna yang akan dicatat
        if employee_id is None:
            # Jika dipanggil dari create, ambil nilai field yang baru
            current_employee_id = self.employee_user_id.id
        elif employee_id is False:
            # Jika pengosongan, catat bahwa pengguna adalah False
            current_employee_id = False
        else:
            # Jika dipanggil dari write, ambil nilai yang diupdate (employee_id)
            current_employee_id = employee_id

        # Hanya buat history jika ada pengguna yang terdefinisi atau dikosongkan
        if current_employee_id or transaction_name == 'User Removal':
            self.env['tw.asset.user.history'].create({
                'asset_id': self.id,
                'employee_id': current_employee_id,
                'transaction_name': transaction_name,
            })
        return True
    
    def unlink_employee_user_id(self):
        self.employee_user_id = False
        return True
    
    def _compute_board_amount(self, sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date):
        # Custom Linear Logic
        if self.method == 'linear':
            # Standard amount per period based on TOTAL life (not remaining)
            # amount_to_depr is (value - salvage), but if we want strictly based on Gross Value for "Standard", 
            # usually it is (self.value - self.salvage_value) / self.method_number.
            # However, standard Odoo linear is: amount_to_depr / (undone_dotation_number - len(posted)) which adapts.
            # Our Requirement: 
            #   Standard Amount = New Value / Total Periods. 
            #   Catch up on the FIRST UNPOSTED line.
            
            # Use 'value' or 'amount_to_depr'? User example: 13.2m / 24. 
            # If salvage is 0, these are same. Assuming standard amount based on Current Total Value.
            # If amount_to_depr is the *remaining* amount to depreciate passed by caller, we should be careful.
            # Caller passes 'amount_to_depr' which usually is 'value_residual' at start of loop.
            # But for Calculation we need the "Generic Period Amount".
            
            # Re-calculating the standard full-period amount based on current asset settings
            total_depreciable_value = self.value - self.salvage_value
            standard_period_amount = total_depreciable_value / self.method_number
            
            # Check if this is the FIRST unposted line being calculated.
            # posted_depreciation_line_ids are the lines ALREADY posted.
            # sequence is the current line number (1-based index of all lines).
            # If we have 3 posted lines, len is 3. The next line is sequence 4.
            next_sequence_to_post = len(posted_depreciation_line_ids) + 1
            
            if sequence == next_sequence_to_post:
                # This is the "Catch-up" line.
                # Calculate what SHOULD have been posted ideally
                theoretical_posted = standard_period_amount * len(posted_depreciation_line_ids)
                
                # Calculate what WAS actually posted
                actual_posted = sum(line.amount for line in posted_depreciation_line_ids)
                
                # Difference to adjust
                diff = theoretical_posted - actual_posted
                
                amount = standard_period_amount + diff
            elif sequence == undone_dotation_number:
                 # Last line: make sure we depreciate exactly the remaining residual
                 # residual_amount passed in is the remaining value BEFORE this line.
                 amount = residual_amount
            else:
                # Standard line
                amount = standard_period_amount
                
            return amount
            
        return super(TwAccountAssetAsset, self)._compute_board_amount(
            sequence, residual_amount, amount_to_depr, undone_dotation_number, 
            posted_depreciation_line_ids, total_days, depreciation_date
        )
    
class TwAccountAssetDepreciationLine(models.Model):
    _inherit = "account.asset.depreciation.line"

    def create_move(self, post_move=True):
        # Call the original create_move which creates the journal entries
        res = super(TwAccountAssetDepreciationLine, self).create_move(post_move=post_move)
        
        # Override: Always post the created moves if post_move is True 
        # (ignoring the category's open_asset configuration)
        if post_move and res:
            moves = self.env['account.move'].browse(res)
            unposted_moves = moves.filtered(lambda m: m.state == 'draft')
            if unposted_moves:
                unposted_moves.action_post()
        return res