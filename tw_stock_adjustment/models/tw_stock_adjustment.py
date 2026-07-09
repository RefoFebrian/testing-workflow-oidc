# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from datetime import datetime


class TwStockAdjustment(models.Model):
    """
    Stock Adjustment model for managing inventory corrections with approval workflow.
    
    Workflow:
    - Draft: Initial state, can add/modify lines
    - Confirm: Lines are generated/validated, ready for processing
    - Done: Adjustment is applied to stock.quant
    - Cancelled: Adjustment is cancelled
    """
    _name = "tw.stock.adjustment"
    _description = "Stock Adjustment"
    _order = "id DESC"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Default methods
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False
    
    def _get_default_location(self):
        if self.company_id:
            warehouse = self.env['stock.warehouse'].suspend_security().search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if warehouse:
                return warehouse.lot_stock_id.id
        return False

    # Fields
    name = fields.Char(
        string='Reference', 
        index='trigram', 
        compute='_compute_name', 
        store=True,
        readonly=True
    )
    date = fields.Date(
        string='Date', 
        default=_get_default_datetime,
        required=True,
        tracking=True
    )
    notes = fields.Text(string='Notes')
    
    # State fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)
    
    # Division
    division = fields.Selection(
        selection=lambda self: self.env['tw.selection'].get_division_options(),
        string='Division',
        required=True,
        tracking=True
    )
    is_all_product = fields.Boolean(
        string='All Product?',
        default=False,
        help='If checked, all products from stock.quant will be generated on Confirm'
    )
    
    # Relation fields
    company_id = fields.Many2one(
        comodel_name='res.company', 
        string='Branch', 
        default=_get_default_branch, 
        domain=[('parent_id', '!=', False)],
        required=True,
        tracking=True
    )
    location_id = fields.Many2one(
        comodel_name='stock.location', 
        string='Location',
        domain="[('company_id', '=', company_id), ('usage', '=', 'internal')]",
        required=True,
        tracking=True
    )
    line_ids = fields.One2many(
        comodel_name='tw.stock.adjustment.line',
        inverse_name='adjustment_id',
        string='Adjustment Lines',
        copy=True
    )
    
    # Summary computed fields
    total_lines = fields.Integer(
        string='Total Lines', 
        compute='_compute_summary', 
        store=True
    )
    total_difference_qty = fields.Float(
        string='Total Difference Qty',
        compute='_compute_summary',
        store=True
    )
    total_difference_value = fields.Float(
        string='Total Difference Value',
        compute='_compute_summary',
        store=True,
        digits='Product Price'
    )
    stock_move_count = fields.Integer(
        string='Stock Moves',
        compute='_compute_stock_move_count'
    )
    journal_entry_count = fields.Integer(
        string='Journal Entries',
        compute='_compute_journal_entry_count'
    )
    valuation_layer_count = fields.Integer(
        string='Valuation Layers',
        compute='_compute_valuation_layer_count'
    )
    
    # Audit fields
    confirm_uid = fields.Many2one('res.users', string='Confirmed by', readonly=True, copy=False)
    confirm_date = fields.Datetime(string='Confirmed on', readonly=True, copy=False)
    done_uid = fields.Many2one('res.users', string='Validated by', readonly=True, copy=False)
    done_date = fields.Datetime(string='Validated on', readonly=True, copy=False)
    cancel_uid = fields.Many2one('res.users', string='Cancelled by', readonly=True, copy=False)
    cancel_date = fields.Datetime(string='Cancelled on', readonly=True, copy=False)

    # Compute methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            record.name = False
            if record.id and record.company_id:
                code = record.company_id.code or 'E'
                prefix = 'ADJ'
                record.name = record.env['ir.sequence'].suspend_security().get_sequence_code(prefix, code)

    @api.depends('line_ids', 'line_ids.difference', 'line_ids.value_difference')
    def _compute_summary(self):
        for record in self:
            record.total_lines = len(record.line_ids)
            record.total_difference_qty = sum(record.line_ids.mapped('difference'))
            record.total_difference_value = sum(record.line_ids.mapped('value_difference'))

    def _compute_stock_move_count(self):
        for record in self:
            record.stock_move_count = self.env['stock.move'].search_count([
                ('origin', '=', record.name)
            ])

    def _compute_journal_entry_count(self):
        for record in self:
            # Get stock moves with origin = adjustment name
            moves = self.env['stock.move'].search([('origin', '=', record.name)])
            # Get account moves from stock valuation layers
            valuation_layers = self.env['stock.valuation.layer'].search([
                ('stock_move_id', 'in', moves.ids)
            ])
            record.journal_entry_count = len(valuation_layers.mapped('account_move_id'))

    def _compute_valuation_layer_count(self):
        for record in self:
            moves = self.env['stock.move'].search([('origin', '=', record.name)])
            record.valuation_layer_count = self.env['stock.valuation.layer'].search_count([
                ('stock_move_id', 'in', moves.ids)
            ])

    # Onchange methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.location_id = False
        self.is_all_product = False
        self.line_ids = [(5, 0, 0)]  # Clear all lines
        if self.company_id:
            warehouse = self.env['stock.warehouse'].suspend_security().search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if warehouse:
                self.location_id = warehouse.lot_stock_id.id

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.state == 'draft':
            self.is_all_product = False
            self.line_ids = [(5, 0, 0)]  # Clear all lines

    @api.onchange('division')
    def _onchange_division(self):
        if self.state == 'draft':
            self.is_all_product = False
            self.line_ids = [(5, 0, 0)]  # Clear all lines

    @api.onchange('is_all_product')
    def _onchange_is_all_product(self):
        if self.state == 'draft':
            if self.is_all_product:
                # Generate all stock lines when checked
                self._generate_all_stock_lines()
            else:
                # Clear lines when unchecked
                self.line_ids = [(5, 0, 0)]

    # CRUD methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(TwStockAdjustment, self).create(vals_list)
    
    def write(self, vals):
        return super(TwStockAdjustment, self).write(vals)
    
    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'cancelled'):
                raise Warning(_("Cannot delete adjustment that is not in Draft or Cancelled state."))
        return super(TwStockAdjustment, self).unlink()

    # Action methods

    def action_confirm(self):
        """
        Confirm the adjustment. Lines can no longer be added/removed.
        """
        self.ensure_one()
        if self.state != 'draft':
            raise Warning(_("Can only confirm from Draft state."))
        
        if not self.line_ids:
            raise Warning(_("Cannot confirm adjustment without lines."))
            
        # Validate lines
        for line in self.line_ids:
            if line.qty_counted is False or line.qty_counted is None:
                raise Warning(_("Line for product %s must have a counted quantity.") % line.product_id.display_name)
            if not line.adjustment_cost:
                raise Warning(_("Line for product %s must have an adjustment cost.") % line.product_id.display_name)
            
            # Validate serial tracking - if product tracking is serial, lot must be filled
            if line.product_id.tracking == 'serial' and not line.lot_id:
                raise Warning(_(
                    "Lot/Serial Number wajib diisi untuk product %s karena produk menggunakan tracking serial."
                ) % line.product_id.display_name)
        
        self.suspend_security().write({
            'state': 'confirm',
            'confirm_uid': self.env.uid,
            'confirm_date': self._get_default_datetime(),
        })

    def _generate_all_stock_lines(self):
        """
        Generate adjustment lines from stock.quant based on location and division.
        Similar to get_stock_available query pattern.
        Only creates lines for product/lot combinations that don't already exist.
        """
        self.ensure_one()
        if not self.location_id:
            raise Warning(_("Please select a location first."))
        
        # Get existing product/lot combinations to skip
        existing_combinations = set()
        for line in self.line_ids:
            key = (line.product_id.id, line.lot_id.id if line.lot_id else False)
            existing_combinations.add(key)
        
        # Get child locations (include sublocations)
        location_ids = self.env['stock.location'].suspend_security().search([
            ('id', 'child_of', self.location_id.id)
        ]).ids
        
        # Get quants with proper domain like get_stock_available
        domain = [
            ('company_id', '=', self.company_id.id),
            ('location_id', 'in', location_ids),
            ('quantity', '>', 0),
            '|',
            ('lot_id', '=', False),
            ('lot_id.state', '=', 'stock'),
        ]
        
        # Filter by division if needed
        if self.division:
            domain.append(('product_id.division', '=', self.division))
        
        quants = self.env['stock.quant'].suspend_security().search(domain)
        
        if not quants:
            raise Warning(_("No stock found in location %s for division %s.") % (
                self.location_id.complete_name, self.division or 'All'
            ))
        
        # Create lines from quants (skip existing product/lot combinations)
        # Use One2many command tuples for onchange compatibility
        line_commands = []
        for quant in quants:
            key = (quant.product_id.id, quant.lot_id.id if quant.lot_id else False)
            if key in existing_combinations:
                continue  # Skip if already exists
            
            line_commands.append((0, 0, {
                'product_id': quant.product_id.id,
                'lot_id': quant.lot_id.id if quant.lot_id else False,
                'location_id': quant.location_id.id,
                'qty_system': quant.quantity,
                'qty_counted': quant.quantity,
                'system_cost': quant.value / quant.quantity if quant.quantity else quant.product_id.standard_price,
                'adjustment_cost': quant.value / quant.quantity if quant.quantity else quant.product_id.standard_price,
            }))
        
        if line_commands:
            self.line_ids = line_commands

    def action_done(self):
        """
        Validate the adjustment and apply to stock.quant.
        This creates stock.move and stock.valuation.layer automatically.
        """
        self.ensure_one()
        if self.state not in ('confirm', 'approved'):
            raise Warning(_("Can only validate from Confirmed or Approved state."))
        
        # Process each line with difference
        lines_with_diff = self.line_ids.filtered(lambda l: l.difference != 0)
        
        if not lines_with_diff:
            raise Warning(_("No lines with quantity difference to adjust."))
        
        for line in lines_with_diff:
            line._apply_adjustment()
        
        self.suspend_security().write({
            'state': 'done',
            'done_uid': self.env.uid,
            'done_date': self._get_default_datetime(),
        })

    def action_cancel(self):
        """
        Cancel the adjustment.
        """
        self.ensure_one()
        if self.state == 'done':
            raise Warning(_("Cannot cancel adjustment that is already done."))
        
        self.suspend_security().write({
            'state': 'cancelled',
            'cancel_uid': self.env.uid,
            'cancel_date': self._get_default_datetime(),
        })

    def action_set_to_draft(self):
        """
        Reset to draft state (only from cancelled).
        """
        self.ensure_one()
        if self.state != 'cancelled':
            raise Warning(_("Can only reset to draft from Cancelled state."))
        
        self.suspend_security().write({
            'state': 'draft',
            'confirm_uid': False,
            'confirm_date': False,
            'cancel_uid': False,
            'cancel_date': False,
        })

    def action_view_stock_moves(self):
        """
        View stock moves created by this adjustment.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Moves'),
            'res_model': 'stock.move',
            'view_mode': 'list,form',
            'domain': [('origin', '=', self.name)],
            'context': {'create': False},
        }

    def action_view_journal_entries(self):
        """
        View journal entries created by this adjustment.
        """
        self.ensure_one()
        moves = self.env['stock.move'].search([('origin', '=', self.name)])
        valuation_layers = self.env['stock.valuation.layer'].search([
            ('stock_move_id', 'in', moves.ids)
        ])
        account_move_ids = valuation_layers.mapped('account_move_id').ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', account_move_ids)],
            'context': {'create': False},
        }

    def action_view_valuation_layers(self):
        """
        View valuation layers created by this adjustment.
        """
        self.ensure_one()
        moves = self.env['stock.move'].search([('origin', '=', self.name)])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Valuation Layers'),
            'res_model': 'stock.valuation.layer',
            'view_mode': 'list,form',
            'domain': [('stock_move_id', 'in', moves.ids)],
            'context': {'create': False},
        }

    def action_download_import_template(self):
        """
        Download Excel template for importing Stock Adjustments.
        Uses tw.format.upload to serve the template file.
        """
        format_upload = self.env['tw.format.upload'].suspend_security().search([
            ('name', '=', 'stock adjustment'),
            ('active', '=', True)
        ], limit=1)
        
        if format_upload:
            return {
                'type': 'ir.actions.act_url',
                'name': 'Download Template',
                'url': f'/web/content/tw.format.upload/{format_upload.id}/file_format_show/{format_upload.filename_upload_format}'
            }
        else:
            raise Warning(_("Format template 'stock adjustment' tidak tersedia. Silakan hubungi Admin untuk membuat template import."))
