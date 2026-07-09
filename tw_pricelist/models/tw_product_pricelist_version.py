# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, time
import pytz
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class ProductPricelistVersion(models.Model):
    _name = "tw.product.pricelist.version"
    _inherit = ["tw.attachment.mixin"]
    _description = 'Product Pricelist Version'

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    # 8: fields
    name = fields.Char('Version Name', required=True)
    # TODO: Apa harus diubah saja ke Datetime?
    date_start = fields.Date ('Start Date', required=True)
    date_end = fields.Date ('End Date', required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Active')], string="State", default='draft')
    expiration_state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('approved', 'Approved'), ('confirmed', 'Active'), ('expired', 'Expired')], string="Expiration State", default='draft', compute='_compute_expiration_state')
    active = fields.Boolean('Active', default=True, help="Active Pricelist Versions")

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', 'Confirmed By')
    confirm_date = fields.Datetime('Confirmed On')

    # 9: relation fields
    pricelist_id = fields.Many2one('product.pricelist', string="Price List", ondelete='cascade', required=True)
    area_id = fields.Many2one('res.area', string='Area', help='Pilih area jika pricelist hanya berlaku di area tertentu saja')
    plate_id = fields.Many2one(comodel_name='tw.selection', string='Plate', domain=[('type', '=', 'PlateType')])
    item_ids = fields.One2many('product.pricelist.item', 'pricelist_version_id', string="Price List Items",required=True, copy=True)

    # 10: constraints & sql constraints
    @api.constrains('state','date_start', 'date_end', 'pricelist_id', 'item_ids', 'plate_id')
    def _check_date(self):
        for version in self:
            duplicate_pricelist = self.search([
                ('pricelist_id', '=', version.pricelist_id.id),
                ('id', '!=', version.id),  # Exclude the current version
                ('name', '=', version.name),
                ('area_id', '=', version.area_id.id),
                ('plate_id', '=', version.plate_id.id)
            ],limit=1)
            if duplicate_pricelist:
                raise exceptions.ValidationError(
                        f"Pricelist Version {version.name} sudah ada pada {duplicate_pricelist.pricelist_id.name} "   
                    )

            # Cek apakah ada versi lain dalam pricelist
            overlapping_versions = self.search([
                ('pricelist_id', '=', version.pricelist_id.id),
                ('id', '!=', version.id),  # Exclude the current version
                ('area_id', '=', version.area_id.id),
                ('plate_id', '=', version.plate_id.id),
                '|', ('date_end', '=', False), ('date_end', '>=', version.date_start),
                '|', ('date_start', '=', False), ('date_start', '<=', version.date_end),
            ],limit=1)

            if overlapping_versions:
                raise exceptions.ValidationError(
                    f"Pricelist Version {version.name} memiliki Periode yang tumpang tindih (overlapping) "
                    f"dengan versi {overlapping_versions.name} di Pricelist {version.pricelist_id.name}."
                )

    # 11: compute/depends & on change methods
    def _compute_expiration_state(self):
        for version in self:
            if version.state != 'confirmed':
                version.expiration_state = version.state
            elif version.date_end < fields.Date.today():
                version.expiration_state = 'expired'
            else:
                version.expiration_state = 'confirmed'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Write Product Pricelist Item (date_start, date_end) from pricelist version                        
            date_start = vals.get('date_start')
            date_end = vals.get('date_end')
            for item in self.item_ids:
                # Update Product Pricelist Item
                item.suspend_security().write(
                    {
                        'date_start': date_start,
                        'date_end': date_end,
                    }
                )
        return super().create(vals_list)
    
    def write(self,vals):
        if vals.get('date_end'):
            # Convert the incoming value to an Odoo date object
            new_date_end = fields.Date.from_string(vals['date_end'])
            # Calculate "yesterday"
            yesterday = fields.Date.today() - relativedelta(days=1)
            # Compare
            if new_date_end < yesterday:
                raise Warning(("Date End cannot be set before yesterday."))

        # Write Product Pricelist Item (date_start, date_end) from pricelist version                        
        date_start = vals.get('date_start') or self.date_start
        date_end = vals.get('date_end') or self.date_end
        for item in self.item_ids:
            # Update Product Pricelist Item
            item.suspend_security().write(
                {
                    'date_start': date_start,
                    'date_end': date_end,
                }
            )
        
        # Update Product Supplierinfo
        supplier_info_obj = self.env['product.supplierinfo'].suspend_security().search([
            ('pricelist_version_id','=',self.id)
        ])
        
        for supplier in supplier_info_obj:
            supplier.write(
                {
                    'date_start': date_start,
                    'date_end': date_end,
                }
            )       

        return super().write(vals)
    
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(('Cannot delete records other than draft !'))
        return super().unlink()
    
    def copy(self, default={}):
        item_ids = []
        for version in self:
            new_date = version.date_end + relativedelta(days=1)
            new_date_end = version.date_end + relativedelta(days=2)
            for lines in version.item_ids:
                item_ids.append([0, 0, {
                    'product_id': lines.product_id.id,
                    'product_tmpl_id': lines.product_tmpl_id.id,
                    'compute_price': lines.compute_price,
                    'fixed_price': lines.fixed_price,
                    'applied_on': lines.applied_on,
                    'categ_id': lines.categ_id.id,
                    'date_start': new_date,
                    'date_end': new_date_end,
                }])
            
            default.update({                  
                'state': 'draft',
                'active': True,
                'date_start': new_date,
                'date_end': new_date_end,
                'name': version.name + ' (Copy)',
                'item_ids': item_ids,
            })
                
        return super().copy(default=default)

    # 12: override methods

    # 13: action methods
    def action_set_to_draft(self):
        self.write(
            {
                'state': 'draft'
            }
        )
    
    def action_copy(self):
        trx = self.copy()
        form_id = self.env.ref('tw_pricelist.tw_product_pricelist_version_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Copy Pricelist Version'),
            'res_model': 'tw.product.pricelist.version',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target':'new',
            'res_id': trx.id,
        }

    def action_confirm(self):
        self._validate_pricelist_version()
        self.write({
            'state': 'confirmed',
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_date()
        })
        self.generate_product_supplierinfo()

    def action_add_new_item(self):
        form_id = self.env.ref('tw_pricelist.tw_pricelist_new_item_wizard_view').id        
        return {
            'type': 'ir.actions.act_window',
            'name': ('Add Item'),
            'res_model': 'tw.product.pricelist.new.item',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target':'new',
            'context': {
                'default_pricelist_id': self.pricelist_id.id,
                'default_pricelist_version_id': self.id,
                'default_date_start': self.date_start,
                'default_date_end': self.date_end,
                'default_type': self.pricelist_id.type,
            }
        }
    
    def action_view_pricelist_items(self):
        list_id = self.env.ref('tw_pricelist.tw_product_pricelist_item_inherit_list_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Pricelist Items'),
            'res_model': 'product.pricelist.item',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [(list_id, 'list')],
            'target':'new',
            'domain': [('pricelist_version_id', '=', self.id)],
        }
    
    # 14: private methods
    def _validate_pricelist_version(self):
        if self.state == 'confirmed':
            raise Warning("State sudah bukan Draft")
        if not self.item_ids:
            raise Warning("Tambahkan Item terlebih dahulu")

    def generate_product_supplierinfo(self,partner=False):
        if not partner:
            # * Ambil default dari partner dengan tags ATPM
            partner = self.env['res.partner'].suspend_security().search(
                [
                    ('category_id.name','=','ATPM')
                ]
            )
            if len(partner) > 1:
                raise exceptions.ValidationError(
                    'Partner ATPM Lebih dari Satu'
                )
            
        for item in self.item_ids:            
            # Tentukan kriteria pencarian data yang sudah ada
            domain = [
                ('pricelist_version_id', '=', self.id),
                ('partner_id', '=', partner.id if partner else self.env['res.users'].sudo().browse(self._uid).partner_id.id),
                ('product_id', '=', item.product_id.id),
            ]
            
            # Cari apakah data sudah ada
            existing_record = self.env['product.supplierinfo'].sudo().search(domain, limit=1)            

            # Persiapkan dictionary data yang akan digunakan
            vals = {
                'pricelist_version_id': self.id,
                'partner_id': partner.id if partner else self.env['res.users'].sudo().browse(self._uid).partner_id.id,
                'company_id': partner.company_id.id if partner else self.env['res.users'].sudo().browse(self._uid).company_id.id,
                'product_name': item.product_tmpl_id.name,
                'product_code': item.product_tmpl_id.default_code,
                'product_tmpl_id': item.product_tmpl_id.id,
                'product_id': item.product_id.id,
                'service_category_id': item.service_category_id.id,
                'cost_based_on_id': item.cost_based_on_id.id,
                'min_qty': item.min_quantity,
                'price': item.fixed_price,
                'discount': item.price_discount,
                'date_start': self.date_start,
                'date_end': self.date_end,
            }

            # Jika sudah ada record, lakukan write
            if existing_record:
                existing_record.sudo().write(vals)
            else:
                # Jika belum ada record, lakukan create
                self.env['product.supplierinfo'].sudo().create(vals)


class TwProductPricelistNewItem(models.TransientModel):
    _name = "tw.product.pricelist.new.item"
    _description = "Add a new item"

    pricelist_id = fields.Many2one('product.pricelist', string="Price List", required=True)
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    item_ids = fields.One2many('product.pricelist.item', 'pricelist_version_id', string="Price List Items", required=True, copy=True)

    def action_new_item(self): 
        # Generate Supplier Infor for New Items   
        self.env['tw.product.pricelist.version'].browse(self._context.get('default_pricelist_version_id')).suspend_security().generate_product_supplierinfo()