# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountAssetCategory(models.Model):
    _inherit = "account.asset.category"
    
    # 7: defaults methods

    # 8: fields
    asset_code = fields.Char(string='Asset Code', help="Prefix code for asset numbering (e.g., OEIT for Office Equipment IT)", compute='_compute_asset_code')
    is_cip = fields.Boolean(string="Is CIP", help="This field is used to identify the type of asset")
    type_assets = fields.Selection(related='account_asset_id.account_type', string='Type Assets')
    
    # 9: relation fields
    asset_code_id = fields.Many2one('tw.selection', string='Asset Code', domain=[('type', '=', 'AssetCode')], help="Prefix code for asset numbering (e.g., OEIT for Office Equipment IT)")
    sequence_id = fields.Many2one('ir.sequence', string='Asset Sequence', copy=False,
                                   help="Sequence used for generating asset codes. Auto-created if not set.")
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('asset_code_id')
    def _compute_asset_code(self):
        for data in self:
            data.asset_code = data.asset_code_id.value if data.asset_code_id else ''

    # 12: override methods   
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Set default values for prepaid categories
            if vals.get('type_assets') == 'asset_prepayments' and 'account_asset_id' not in vals:
                # You might want to set default accounts for prepaid categories
                pass
        return super(InheritAccountAssetCategory, self).create(vals_list)

    def write(self, vals):
        # Prevent changing type if there are assets using this category
        if 'type_assets' in vals and any(asset.state != 'draft' for asset in self.asset_ids):
            raise UserError(_("You cannot change the type of a category that has assets not in draft state."))
        return super(InheritAccountAssetCategory, self).write(vals)

    @api.onchange('account_asset_id')
    def _onchange_account_assets(self):
        type_asset = ["asset_receivable", "asset_cash", "asset_current", "asset_non_current", "asset_prepayments", "asset_fixed"]
        for data in self:
            if data.type_assets and data.type_assets not in type_asset:
                raise Warning("Tolong pilih Account dengan tipe Assets")
    
    # 14: private methods
    def _get_or_create_sequence(self):
        """Get or create sequence for this asset category."""
        self.ensure_one()
        if not self.sequence_id:
            prefix = self.asset_code or 'ASSET'
            sequence_vals = {
                'name': f'Asset Sequence - {self.name}',
                'code': f'account.asset.{self.id}',
                'prefix': prefix,
                'padding': 9,
                'number_next': 1,
                'number_increment': 1,
                'company_id': False,  # Shared across companies
            }
            sequence = self.env['ir.sequence'].sudo().create(sequence_vals)
            self.sudo().write({'sequence_id': sequence.id})
        return self.sequence_id
    
    def get_next_asset_code(self):
        """
        Generate next asset code for this category.
        Format: {asset_code}{sequence} e.g., OEIT000000001
        """
        self.ensure_one()
        sequence = self._get_or_create_sequence()
        return sequence.next_by_id()

