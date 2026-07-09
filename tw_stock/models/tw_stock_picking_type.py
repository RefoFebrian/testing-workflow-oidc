# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, timedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"
    
    # 7: defaults methods

    # 8: fields
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    auto_batch = fields.Boolean('Automatic Batches', default=False, help="Automatically put pickings into batches as they are confirmed when possible.")
    batch_sequence_code = fields.Char(
        string="Batch Sequence Code",
        default='BATCH',
        required=True,
        help="Code Sequence yang digunakan ketika Generate Name Batch Transfer."
    )
    is_create_batch_next_step = fields.Boolean('Create Batch Next Step', default=False, help="Automatically put pickings into batches as they are confirmed when possible.")
    is_create_batch_backorder = fields.Boolean('Create Batch Backorder', default=False, help="Automatically put backorders into batches as they are confirmed when possible.")
    is_auto_create_batch_line = fields.Boolean('Auto Create Batch Line', default=False, help="Automatically create batch line when create batch.")
    is_validate_batch_line = fields.Boolean('Validate Batch Line', default=False, help="Custom process validate batch line.")
    is_need_location = fields.Boolean('Need Location', default=False, help="Need location when process batch line.")
    default_qty = fields.Selection([
        ('auto','Auto'),
        ('manual','Manual'),
    ], string='Default Qty')
    
    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch")
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods 
    @api.depends('code')
    def _compute_use_create_lots(self):
        for picking_type in self:
            if picking_type.code == 'incoming':
                if picking_type.use_existing_lots:
                    picking_type.use_create_lots = False
                elif picking_type.use_create_lots:
                    picking_type.use_existing_lots = False
            
            # ? Pengeluaran hanya menggunakan existing lot
            elif picking_type.code == 'outgoing':
                picking_type.use_create_lots = False
                picking_type.use_existing_lots = True

    @api.onchange('use_existing_lots')
    def _onchange_use_existing_lots(self):
        for picking_type in self:
            if picking_type.code == 'incoming':
                if not picking_type.use_existing_lots:
                    picking_type.use_create_lots = True    
    
    @api.onchange('use_create_lots')
    def _onchange_use_create_lots(self):
        for picking_type in self:
            if picking_type.code == 'incoming':
                if not picking_type.use_create_lots:
                    picking_type.use_existing_lots = True    
    
    @api.onchange('code', 'use_existing_lots', 'use_create_lots')
    def _check_use_lots(self):
        """Ensure only one of use_existing_lots or use_create_lots is True for incoming picking types.
        
        If neither is selected, defaults to use_create_lots = True.
        """
        for picking_type in self:
            if not picking_type.name:
                continue
            if picking_type.code == 'incoming':
                if picking_type.use_existing_lots and picking_type.use_create_lots:
                    raise ValidationError(_('You cannot select both "Create New Lots/Serial Numbers" and "Use Existing Lots/Serial Numbers" at the same time.'))

    @api.onchange('batch_sequence_code')
    def _onchange_batch_sequence_code(self):
        if self.batch_sequence_code:
            self.batch_sequence_code = self.batch_sequence_code.upper()
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('batch_sequence_code'):
                vals['batch_sequence_code'] = vals['batch_sequence_code'].upper()
        create = super(StockPickingType, self).create(vals_list)
        create._check_use_lots()
        return create

    def write(self, vals):
        if vals.get('batch_sequence_code'):
            vals['batch_sequence_code'] = vals['batch_sequence_code'].upper()
        return super(StockPickingType, self).write(vals)
    
    # 13: action methods

    # 14: private methods

    def _build_picking_type_domain(self, code, warehouse_id, division, use_create_lots, additional_domain=[]):
        """Build domain for searching picking type.
        
        Args:
            code: Picking type code ('incoming', 'outgoing', 'internal', 'mrp_operation')
            warehouse_id: Warehouse record ID
            division: Division value or False
            use_create_lots: Boolean for use_create_lots filter
            
        Returns:
            list: Domain for stock.picking.type search
        """
        domain = [
            ('code', '=', code),
            ('division', '=', division),
            ('warehouse_id', '=', warehouse_id),
            ('use_create_lots', '=', use_create_lots),
            *additional_domain,
        ]
        return domain

    @api.model
    def get_picking_type(self, code, company_id, division='Unit', is_create=False, limit=1, additional_domain=[]):
        """Get picking type based on code, company, and division.
        
        Args:
            code: Picking type code ('incoming', 'outgoing', 'internal', 'mrp_operation')
            company_id: Company/Branch record ID
            division: Division ('Unit', 'Sparepart', 'Service', 'Umum')
            is_create: Flag for creation context (unused currently)
            limit: Maximum records to return
            
        Returns:
            stock.picking.type recordset
            
        Raises:
            UserError: If no warehouse configured for non-stock managers
            RedirectWarning: If no warehouse configured for stock managers
            ValidationError: If no matching picking type found
        """
        branch = self.env['res.company'].browse(company_id)
        company_warehouse_obj = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        
        if not company_warehouse_obj:
            warehouse_action = self.env.ref('stock.action_warehouse_form')
            msg = _('Please create a warehouse for company %s.', branch.name)
            if not self.env.user.has_group('stock.group_stock_manager'):
                raise UserError('Please contact your administrator to configure your warehouse.')
            raise RedirectWarning(msg, warehouse_action.id, _('Go to Warehouses'))
        
        # Determine use_create_lots based on branch setting and code
        if self._context.get('is_asset'):
            use_create_lots = False
        elif branch.is_supplier_is_internal and code == 'incoming':
            use_create_lots = False
        elif code == 'internal':
            use_create_lots = False
        elif code == 'outgoing':
            use_create_lots = False
        else:
            use_create_lots = True

        # Search with specified division first
        domain_search = self._build_picking_type_domain(code, company_warehouse_obj.id, division, use_create_lots, additional_domain)
        picking_type_obj = self.search(domain_search, limit=limit)
        
        # Fallback: search without division filter
        if not picking_type_obj:
            domain_search = self._build_picking_type_domain(code, company_warehouse_obj.id, False, use_create_lots, additional_domain)
            picking_type_obj = self.search(domain_search, order="id", limit=limit)
        
        if not picking_type_obj:
            if not is_create:
                raise ValidationError(_(
                    'No picking type found for %s on division %s in branch %s\n'
                    'Settings: Create Lots (%s), Warehouse (%s)\n'
                    'Additional Domain: %s',
                    code, division, branch.name, use_create_lots, company_warehouse_obj.name, str(additional_domain)
                ))
        
        return picking_type_obj