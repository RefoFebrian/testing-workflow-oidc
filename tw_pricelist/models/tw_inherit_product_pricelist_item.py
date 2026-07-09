# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, time
import pytz
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # 7: defaults methods
    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)

        user_tz_name = self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(user_tz_name)

        # Helper to localize date and time to user tz, then get UTC
        def localize_to_utc(date_obj, hh=0, mm=0, ss=0):
            """Return a UTC datetime string from a date_obj and local hh:mm:ss."""
            local_dt = user_tz.localize(datetime.combine(date_obj, time(hh, mm, ss)), is_dst=None)
            utc_dt = local_dt.astimezone(pytz.UTC)
            return fields.Datetime.to_string(utc_dt)
        
        if 'date_start' in res and not res.get('date_start'):
            raise Warning('Silahkan isi tanggal di Version terlebih dahulu')
        if res.get('date_start'):
            # parse date (string "YYYY-MM-DD") to a date object
            date_part = fields.Date.to_date(res['date_start'])
            if date_part:
                # localize midnight + 1s in user's TZ, then store as UTC
                res['date_start'] = localize_to_utc(date_part, 0, 0, 1)

        if 'date_end' in res and not res.get('date_end'):
            raise Warning('Silahkan isi tanggal di Version terlebih dahulu')
        if res.get('date_end'):
            date_part = fields.Date.to_date(res['date_end'])
            if date_part:
                # localize 23:59:59 in user's TZ, then store as UTC
                res['date_end'] = localize_to_utc(date_part, 23, 59, 59)

        return res

    # 8: fields
    pricelist_type = fields.Selection(related='pricelist_id.type', string='Pricelist Type', store=False)
    cost_based_on_value = fields.Char(related='cost_based_on_id.value', string='Cost Based On Value', store=False)
    is_service = fields.Boolean(string="Is Service", help="Check if the product is a service or not", compute='_compute_is_service')
    previous_price = fields.Float(string="Previous Price", digits='Product Price')
    applied_on = fields.Selection(
        selection=[
            ('3_global', "All Products"),
            ('2_product_category', "Product Category"),
            ('1_product', "Product"),
            ('0_product_variant', "Product Variant"),
        ],
        string="Apply On",
        default='1_product',
        required=True,
        help="Pricelist Item applicable on selected option")

    is_update = fields.Boolean('Is Update?',help="Helper for update price form")
    state = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='state', default='active')
    version_state = fields.Char(string='Version State', compute='_compute_version_state')

    # Audit trail
    inactive_uid = fields.Many2one('res.users', string="Inactive By", readonly=True)
    inactive_date = fields.Datetime(string="Inactive Date", readonly=True)

    # 9: relation fields
    service_category_id =  fields.Many2one(comodel_name='tw.selection', string='Service Category' , domain=[('type','=','PricelistServiceCategory')], help="Field that can be used if the product (Unit) has a service category.")
    cost_based_on_id =  fields.Many2one(comodel_name='tw.selection', string='Cost Based On' , domain=[('type','=','PricelistCategory')], help="Pricelist that can be used for expeditions, if necessary.",)
    pricelist_version_id = fields.Many2one('tw.product.pricelist.version', string="Pricelist Versions", ondelete='cascade', required=True)
    area_id = fields.Many2one('res.area', string='Area', compute='_compute_area', store=True)

    # 10: constraints & sql constraints
    @api.constrains('cost_based_on_id', 'pricelist_id', 'product_tmpl_id', 'product_id')
    def _check_cost_based_on_expedition(self):
        """Validate cost_based_on_id is mandatory for expedition pricelist type.
        Also validate product_tmpl_id is mandatory when cost_based_on is 'product'.
        """
        for rec in self:
            if rec.pricelist_type == 'expedition' and not rec.cost_based_on_id:
                raise exceptions.ValidationError(
                    "'Cost Based On' is required for Expedition pricelist type."
                )
            if rec.cost_based_on_value == 'product' and not rec.product_tmpl_id and not rec.product_id:
                raise exceptions.ValidationError(
                    "'Product' or 'Product Variant' is required when Cost Based On is 'Product'."
                )

    @api.constrains('categ_id', 'product_tmpl_id', 'product_id', 'pricelist_id', 'service_category_id')
    def _check_date(self):
        for pricelist_item in self:
            domain = pricelist_item._get_check_date_constrains_domain()

            # Search for overlapping pricelist versions            
            duplicate_pricelist = self.search(domain)
            if duplicate_pricelist:
                message = pricelist_item._get_check_date_validation_message(duplicate_pricelist)
                raise exceptions.ValidationError(message)

    # 11: compute/depends & on change methods
    @api.onchange('categ_id','product_tmpl_id','product_id')
    def _onchange_product_settings(self):
        if not self.is_update: # Service Category False, after opening Update Price
            self.service_category_id = False
        if self.pricelist_id and self.pricelist_version_id and self.applied_on and self.categ_id and self.product_tmpl_id and self.product_id:
            last_price = self._get_previous_item(self.pricelist_id,self.pricelist_version_id,self.applied_on,self.categ_id,self.product_tmpl_id,self.product_id)
            self.last_price = last_price

    @api.depends('product_tmpl_id', 'product_id', 'categ_id')
    def _compute_is_service(self):
        for record in self:
            record.is_service = False
            if record.product_tmpl_id and (record.product_tmpl_id.categ_id.id in record.product_tmpl_id.categ_id.get_child_ids('Service')):
                record.is_service = True
            elif record.product_id and (record.product_id.categ_id.id in record.product_id.categ_id.get_child_ids('Service')):
                record.is_service = True
            elif record.categ_id and record.categ_id.get_child_ids('Service'):
                record.is_service = True
                
    @api.depends('pricelist_version_id')
    def _compute_version_state(self):
        for record in self:
            if record.pricelist_version_id:
                record.version_state = record.pricelist_version_id.state
            else:
                record.version_state = 'draft'
    
    @api.depends('pricelist_version_id')
    def _compute_area(self):
        for record in self:
            pricelist_version = record.pricelist_version_id
            if pricelist_version:
                record.area_id = pricelist_version.area_id or False
            else:
                record.area_id = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list): 
        # Create From Button New Item
        if self._context.get('active_id') and self._context.get('active_model') == 'tw.product.pricelist.version':
            for vals in vals_list:
                vals['pricelist_version_id'] = self._context.get('active_id')
        
        for vals in vals_list:
            if vals.get('pricelist_version_id') and not vals.get('pricelist_id'):
                vals['pricelist_id'] = self.env['tw.product.pricelist.version'].browse(vals['pricelist_version_id']).pricelist_id.id

            if vals.get('pricelist_version_id') and not vals.get('previous_price'):
                last_price = self._get_previous_item(vals.get('pricelist_id'),vals.get('pricelist_version_id'),vals.get('applied_on'),vals.get('categ_id'),vals.get('product_tmpl_id'),vals.get('product_id'))
                vals['previous_price'] = last_price
                
        return super().create(vals_list)
    
    def write(self,vals):       
        if vals.get('categ_id') or vals.get('product_tmpl_id') or vals.get('product_id'):
            if vals.get('pricelist_version_id',self.pricelist_version_id):
                last_price = self._get_previous_item(vals.get('pricelist_id',self.pricelist_id.id),vals.get('pricelist_version_id',self.pricelist_version_id.id),vals.get('applied_on',self.applied_on),vals.get('categ_id',self.categ_id.id),vals.get('product_tmpl_id',self.product_tmpl_id.id),vals.get('product_id',self.product_id.id))
            vals['previous_price'] = last_price
        write = super().write(vals)
        if self.pricelist_version_id and self.pricelist_version_id.state != 'draft':
            if vals.get('applied_on') or vals.get('fixed_price') or vals.get('compute_price') or vals.get('product_tmpl_id') or vals.get('product_id') or vals.get('base'):
                raise Warning('Gagal! Hanya draft pricelist version yang bisa di edit! Silahkan buat pricelist baru')
        return write
    
    def unlink(self):
        for rec in self:
            if rec.pricelist_version_id and rec.pricelist_version_id.state != 'draft':
                raise Warning('Cannot delete records other than draft !')
        return super().unlink()
    
    @api.onchange("cost_based_on_id")
    def _onchange_cost_based_on_id(self):
        if self.env.context.get('default_is_update'):
            return
        if self.cost_based_on_id:
            self.product_tmpl_id = False
            self.product_id = False

    # 13: action methods
    def action_update_price(self):
        if self.state != 'active':
            raise Warning('State sudah tidak active, silahkan refresh halaman')
        self.ensure_one()
        data = {
            'default_state': 'new',
            'default_is_update': True,
            'default_pricelist_id': self.pricelist_id.id,
            'default_base_pricelist_id': self.base_pricelist_id.id,
            'default_pricelist_version_id': self.pricelist_version_id.id,
            'default_applied_on': self.applied_on,
            'default_categ_id': self.categ_id.id,
            'default_product_tmpl_id': self.product_tmpl_id.id,
            'default_product_id': self.product_id.id,
            'default_service_category_id': self.service_category_id.id,
            'default_cost_based_on_id': self.cost_based_on_id.id,
            'default_fixed_price': self.fixed_price,
            'default_compute_price': self.compute_price,
            'default_base': self.base,
            'default_base_pricelist_id': self.base_pricelist_id.id,
            'default_date_start': self.date_start,
            'default_date_end': self.date_end,
        }
        form_id = self.env.ref('tw_pricelist.tw_product_pricelist_item_form_view').id
        return {
            'name': 'Update Price',
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'form',
            'target': 'new',
            'view_id': form_id,
            'context': data,
        }
    
    def action_confirm_update_price(self):
        self.ensure_one()
        return self._action_confirm_update_price()

    # 14: private methods    
    def _action_inactive(self):
        self.write({
            'state': 'inactive',
            'inactive_uid': self.env.user.id,
            'inactive_date': fields.Datetime.now(),
        })
    
    def _action_active(self):
        self.write({
            'state': 'active',
            'is_update': False,
            'inactive_uid': False,
            'inactive_date': False,
        })
    
    def _action_confirm_update_price(self):
        previous_pricelist = self._get_active_item()
        previous_pricelist._action_inactive()
        self._action_active()
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}
    
    def _get_active_item(self,state=['active','new']):
        domain = [
            ('state', 'in', state),
            ('applied_on', '=', self.applied_on),
            ('pricelist_id', '=', self.pricelist_id.id),
            ('pricelist_version_id', '=', self.pricelist_version_id.id),
            ('service_category_id', '=', self.service_category_id.id),
            ('cost_based_on_id', '=', self.cost_based_on_id.id),
            ('id', '!=', self.id),
        ]
        if self.applied_on == '2_product_category':
            domain.append(('categ_id', '=', self.categ_id.id))
        elif self.applied_on == '1_product':
            domain.append(('product_tmpl_id', '=', self.product_tmpl_id.id))
        elif self.applied_on == '0_product_variant':
            domain.append(('product_id', '=', self.product_id.id))
        
        item = self.search(domain)
        return item
    
    def _get_previous_item(self, pricelist_id, pricelist_version_id, applied_on, categ_id, product_tmpl_id, product_id):
        last_price = 0
        prev_item = self.search([
            ('pricelist_id','=',pricelist_id),
            ('pricelist_version_id.id','<=',pricelist_version_id),
            ('applied_on','=',applied_on),
            ('categ_id','=',categ_id),
            ('product_tmpl_id','=',product_tmpl_id),
            ('product_id','=',product_id),
        ],order='date_end desc',limit=1)
        if prev_item:
            last_price = prev_item.fixed_price
        return last_price
    
    def _get_check_date_constrains_domain(self):
        domain = [
            ('state', '=', 'active'),
            ('state', '=', self.state), #Pengecekan state 'active' dan sel.state dibuat supaya hanya membandingkan state active saja
            ('applied_on', '=', self.applied_on),
            ('pricelist_id', '=', self.pricelist_id.id),
            ('pricelist_version_id', '=', self.pricelist_version_id.id),
            ('service_category_id', '=', self.service_category_id.id),
            ('cost_based_on_id', '=', self.cost_based_on_id.id),
            ('id', '!=', self.id),
        ]
        if self.applied_on == '2_product_category':
            domain.append(('categ_id', '=', self.categ_id.id))
        elif self.applied_on == '1_product':
            domain.extend([
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
                ('product_id', '=', self.product_id.id)
            ])
        elif self.applied_on == '0_product_variant':
            domain.append(('product_id', '=', self.product_id.id))
        
        return domain
    
    def _get_check_date_validation_message(self, duplicate_pricelist):
        pricelist_names = ", ".join(duplicate_pricelist.mapped("pricelist_id.name"))
        pricelist_item_names = ", ".join(duplicate_pricelist.mapped("name"))
        pricelist_item_category = ", ".join(duplicate_pricelist.mapped("service_category_id.name"))
        return f'You cannot have two pricelist items that have the same configuration! ' \
                f'\nConflicting Pricelists: {pricelist_names or False}. ' \
                f'\nConflicting Versions: {duplicate_pricelist.mapped("pricelist_version_id.name") or False}. ' \
                f'\nConflicting Items: {pricelist_item_names or False}. ' \
                f'\nConflicting Product Template: {duplicate_pricelist.mapped("product_tmpl_id.name") or False}. ' \
                f'\nConflicting Product Variant: {duplicate_pricelist.mapped("product_id.name") or False}. ' \
                f'\nConflicting Category: {pricelist_item_category or False}'
    
    def _compute_base_price(self, product, quantity, uom, date, currency):
        price = super(ProductPricelistItem,self)._compute_base_price(product, quantity, uom, date, currency)
        if self.base_pricelist_id:
            self.base_pricelist_id._get_applicable_rules(product,date)

        return price
        