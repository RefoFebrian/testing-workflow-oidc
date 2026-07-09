# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
import qrcode
import base64
import io

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwBarcodeLabelAsset(models.TransientModel):
    _name = "tw.barcode.label.asset"
    _description = 'Tw Barcode Labelling Asset'

    # 8: Fields
    name = fields.Char()
    asset_code_id = fields.Many2one('tw.selection', string='Asset Code', domain=[('type', '=', 'AssetCode')])
    asset_code = fields.Char(compute='_compute_asset_code', string='Asset Code')
    label_state = fields.Selection(selection=[
        ('all', 'All'),
        ('labelled', 'Terlabel'),
        ('unlabelled', 'Tidak'),
    ], default='unlabelled', string='Label Status')

    # 9: Relation Fields
    company_ids = fields.Many2many('res.company', 'tw_asset_barcode_rel', 'tw_asset_barcode_id', 'company_id', "Branch",domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    label_asset_ids = fields.One2many('tw.barcode.label.asset.line', 'label_id')

    # 10: Constraints & SQL Constraints
    
    # 11: Compute/Depends & On Change Methods
    @api.depends('asset_code_id')
    def _compute_asset_code(self):
        for data in self:
            data.asset_code = data.asset_code_id.code if data.asset_code_id else ''


    # 12: Override Methods

    # 13: Action Methods

    def action_listing_asset(self):
        self.label_asset_ids = False
        domain = [('company_id', 'in', self.company_ids.ids)]
        
        if self.label_state == 'labelled':
            domain.append(('is_labelled', '=', True))
        elif self.label_state == 'unlabelled':
            domain.append(('is_labelled', '=', False))

        if self.asset_code_id:
            domain.append(('category_id.asset_code_id', '=', self.asset_code_id.id))

        assets = self.env['account.asset.asset'].suspend_security().search(domain, limit=100)
        # Generate QR codes and convert to base64
        label_asset_ids = []
        for asset in assets:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
            qr.add_data(asset.name)
            qr.make()
            img = qr.make_image(fill='black', back_color='white')

            # Save QR image as base64
            qr_buffer = io.BytesIO()
            img.save(qr_buffer, 'PNG')
            qr_buffer.seek(0)
            label_asset_ids.append([0,0,{
                'label_id': self.id,
                'asset_id': asset.id,
                'asset_name': asset.product_id.name,
                'asset_number': asset.name,
                'asset_code': asset.code,
                'asset_category': asset.category_id.name,
                'purchase_date': asset.purchase_date,
                'division': asset.division,
                'partner': asset.partner_id.name,
                'qr_code_base64': base64.b64encode(qr_buffer.read()).decode(),
                'status': 'labelled' if asset.is_labelled else 'unlabelled'
                }])
        
        self.label_asset_ids = label_asset_ids

    
    def action_print_barcode_label(self):
        active_ids = self.env.context.get("active_ids", [])
        user = self.env['res.users'].suspend_security().browse(self._uid).name
        form_data = self.read()[0]
        form_data['label_asset_ids'] = self.label_asset_ids.suspend_security().search([
            ('is_print', '=', True),
            ('label_id', '=', self.id)
        ]).ids

        if not form_data['label_asset_ids']:
            raise Warning('Setidaknya 1 Asset di checklist print!')

        datas = {
            "ids": active_ids,
            "model": "tw.barcode.label.asset",
            "form": form_data,
            "user": user
        }
        return self.env.ref('tw_asset_barcode.action_print_barcode_label_asset').report_action(self, data=datas)

    def action_checklist_print_asset(self):
        if self.label_asset_ids:
            self.label_asset_ids.sudo().write({'is_print': True})

    # 14: Private Methods

