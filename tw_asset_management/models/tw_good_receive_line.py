# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby

# 5: local imports

# 6: Import of unknown third party lib

class InheritGoodReceiveAsset(models.Model):
    _name = "tw.good.receive.asset.line"
    _description = "Good Receive Asset Line"    

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()

    # 8: fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open','Open'),        
        ('done', 'Done'), 
        ('cancel', 'Cancelled')
        ], default='draft')

    name = fields.Char(string='Name')
    description = fields.Char(string='Material Desc')
    sequence = fields.Integer('Sequence')

    no_do = fields.Char('No DO')
    do_date = fields.Date('DO Date')
    division = fields.Selection([('Umum','Umum')], string='Division', default='Umum', required=True)
    domain_purchase_order_id = fields.Char(string='Domain Purchase Order ID')
    domain_asset_register_id = fields.Char(string='Domain Asset Register ID')
    is_asset = fields.Boolean(string='Asset?',related='product_id.is_asset')
    is_cip = fields.Boolean(related="asset_category_id.is_cip",string='CIP')
    is_final_cip = fields.Boolean('Is Final CIP?')
    is_have_regas = fields.Boolean('Is Have Register Asset?')
    is_acquired = fields.Boolean('Is Fully Acquired?', compute='_compute_acquisition_status', store=True, help="Flag if this line has been fully acquired")
    qty_acquired = fields.Float('Qty Acquired', default=0.0, help="Quantity that has been used in asset acquisition or capitalization")
    qty_acquisition_available = fields.Float('Qty Available for Acquisition', compute='_compute_acquisition_status', store=True)
    supplier_invoice_number = fields.Char(string='Supplier Invoice Number')
    document_date = fields.Date(string='Document Date',default=_get_default_date)
    description = fields.Char(string='Description')
    site = fields.Char(string='Site')
    retensi = fields.Float(string='Retensi')

    display_name = fields.Char(compute='_compute_display_name', store=True)
    

    qty = fields.Float(string='Qty',default=1.0)
    quantity = fields.Float('Quantity', digits='Product Unit of Measure',related='qty', store=True)
    qty_remaining = fields.Integer(string='Qty Remaining')
    qty_receipt = fields.Integer(string='Qty Receipt')
    qty_order = fields.Integer(string='Qty Order')
    qty_available = fields.Integer(string='Qty Available')
    qty_registered = fields.Integer(string='Qty Registered')
    qty_unregistered = fields.Integer(string='Qty Unregistered')

    price = fields.Float(string='Price')
    discount = fields.Float('Discount')
    price_tax = fields.Float(string='Price Tax', digits='Product Price', compute='_compute_subtotal')
    price_subtotal = fields.Float(string='Subtotal', digits='Product Price', compute='_compute_subtotal')
    price_total = fields.Float(string='Amount', digits='Product Price', compute='_compute_subtotal')
    type_assets = fields.Selection(related='asset_category_id.type_assets')
    no_faktur_pajak = fields.Integer(string='No Faktur')
    tgl_faktur_pajak = fields.Date(string='Tgl Faktur Pajak')

    # 9: relation fields   
    purchase_order_id = fields.Many2one('purchase.order.asset',string='Purchase Order')
    purchase_order_line_id = fields.Many2one('purchase.order.asset.line',domain="[('id', '=', False)]",string='Purchase Order Line')
    product_id = fields.Many2one('product.product', string='Product',  help="Product for the operation")
    picking_id = fields.Many2one(comodel_name='tw.good.receive', string='Good Receive', required=True, ondelete='cascade', help="Good Receive Reference")
    picking_type_id = fields.Many2one(related='picking_id.picking_type_id', string='Picking Type', store=True)
    move_id = fields.Many2one('stock.move', ondelete='set null')
    account_move_id = fields.Many2one('account.move', string='Account Move', ondelete='cascade')
    asset_category_id = fields.Many2one('account.asset.category', string='Asset Category', store=True, help="Asset Category for the operation")
    asset_register_id = fields.Many2one('account.asset.asset', string='Asset', ondelete='cascade')
    currency_id = fields.Many2one("res.currency", readonly=True)
    tax_ids = fields.Many2many('account.tax', 'good_receive_line_tax', 'teds_good_receive_line_id', 'tax_id', string='Taxes')           
    location_id = fields.Many2one('stock.location', string='Location')
    location_dest_id = fields.Many2one('stock.location', string='Location Destination')
    company_id = fields.Many2one(related="picking_id.company_id")
    employee_user_id = fields.Many2one("hr.employee",string="Pengguna Asset")
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('sequence', 'product_id', 'product_id.name')
    def _compute_display_name(self):
        for line in self:
            seq = line.sequence or 0
            product_name = line.product_id.name if line.product_id else 'N/A'
            line.display_name = f"{product_name}"

    @api.depends('price','discount')
    def _compute_subtotal(self):
        for line in self:
            currency = line.picking_id.company_id.currency_id
            if not line.price:
                 line.price = line.purchase_order_line_id.price_unit
            price_subtotal = price_total = total = (line.price * line.qty) - line.discount
            tax = 0.0
            
            if line.tax_ids:
                computed_tax = line.tax_ids.compute_all(total, currency)
                price_subtotal = computed_tax.get('total_excluded')
                price_total = computed_tax.get('total_included')
                tax = sum([tax['amount'] for tax in computed_tax['taxes']])

            line.price_tax = tax
            line.price_subtotal = price_subtotal
            line.price_total = price_total

    @api.depends('qty', 'qty_acquired')
    def _compute_acquisition_status(self):
        for line in self:
            line.qty_acquisition_available = max(0.0, line.qty - line.qty_acquired)
            line.is_acquired = float_compare(line.qty_acquired, line.qty, precision_digits=2) >= 0


    @api.onchange('no_do','do_date')
    def _onchange_do_asset(self):
        if self.no_do and self.do_date:
            if self.asset_category_id.is_cip:
                raise Warning('Jika Nomor DO dan Tanggal DO dipilih maka silahkan ganti dahulu asset category selain CIP (Perubahan untuk CIP ke Running)')

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        self.purchase_order_line_id = False
        if self.purchase_order_id:
            # * Domain Register Asset base on PO
            check_gr = self.search([('purchase_order_id', '=', self.purchase_order_id.id),('asset_register_id','!=',False)],limit=1)
            if check_gr:
                if check_gr.is_cip:
                    self.is_have_regas = True
                    self.asset_register_id = check_gr.asset_register_id.id
                    check_po = self.env['purchase.order.asset.line'].search([('order_id', '=', self.purchase_order_id.id),('is_not_fully_received','=',True)])
                    if check_po and len(check_po) > 1:
                        self.is_final_cip = False
                    else:
                        self.is_final_cip = True
                self.domain_asset_register_id = [('id', 'in', check_gr.asset_register_id.ids)]
            else:
                self.is_final_cip = False
                self.is_have_regas = False
                self.asset_register_id = False
                self.domain_asset_register_id = [('id', '=', False)]
            
            self.domain_purchase_order_id = [('is_not_fully_received','=',True),('id', 'in', self.purchase_order_id.order_line.ids)]
            
        else:
            self.domain_purchase_order_id = [('id', '=', False)]
            self.domain_asset_register_id = [('id', '=', False)]

    @api.onchange('purchase_order_line_id')
    def _onchange_purchase_order_line_id(self):
        self.product_id = False
        self.qty_available = self.qty_remaining = 0
        self.price = 0.0
        self.description = False
        check_po_line_id = self.picking_id.move_asset_ids.filtered(lambda x: x.purchase_order_line_id.id == self.purchase_order_line_id.id)
        if len(check_po_line_id) > 1:
            raise Warning("PO Line tidak boleh duplikat!")
        if self.purchase_order_line_id:
            product = self.purchase_order_line_id.product_id.with_company(self.company_id)
            self.qty_available = self.qty_remaining - self.qty
            self.product_id = product.id
            self.asset_category_id = product.asset_category_id
            if self.product_id:
                if not product.asset_category_id and self.is_asset:
                    raise Warning("Asset Category not found, Silahkan setting pada menu Products -> Tab Assets")
                # Warn if CIP category but product is_asset is not checked
                if self.asset_category_id and self.asset_category_id.is_cip and not product.is_asset:
                    return {
                        'warning': {
                            'title': _("Peringatan: Product CIP Belum di-Mark sebagai Asset"),
                            'message': _("Product '%s' memiliki Asset Category CIP tapi checkbox 'Is Asset?' di Product belum dicentang. "
                                         "Ini akan menyebabkan GR Line tidak muncul di pilihan Akuisisi Asset. "
                                         "Silahkan centang 'Is Asset?' di menu Products > Tab Assets.") % self.product_id.display_name
                        }
                    }
            self.qty_available = self.qty_remaining = self.purchase_order_line_id.product_qty
            if self.purchase_order_line_id.qty_received > 0:
                self.qty_available =  self.qty_remaining - self.purchase_order_line_id.qty_received
            self.price = self.purchase_order_line_id.price_unit
            self.tax_ids = self.purchase_order_line_id.taxes_id
            self.description = self.purchase_order_line_id.name.split('\n')[1] if '\n' in self.purchase_order_line_id.name else self.purchase_order_line_id.name

    @api.onchange('qty')
    def _onchange_qty(self):
        if self.qty <= 0:
            raise Warning(_("Product Quantity must be greater than 0!"))
        if self.qty > self.qty_available and self.purchase_order_line_id:
            raise Warning(_("Product Quantity must be less than or equal to Qty Available!"))
        

    # 12: override methods

    def action_open(self):
        return self.write({
            'state': 'open'
        })

    # 13: private methods
    def update_asset(self,register,value=0):
        vals = {}
        if not register:
            raise Warning('REGAS tidak ada, silahkan pilih Asset Register ketika CIP')
        
        if register.category_id.is_cip:
            value = register.value + value
            vals.update({'value': value,'state': 'CIP'})
        
        if self.no_do and self.do_date:
            self.asset_register_id = register.id
            vals.update({'category_id': self.asset_category_id.id})
        register.write(vals)
        
        if self.no_do and self.do_date:
            register.validate()
           

    
    def update_qty_received(self):
        if self.purchase_order_line_id:
            self.purchase_order_line_id.qty_received = self.purchase_order_line_id.qty_received + self.qty

    def asset_create(self,no=0):
        subtotal = self.price
        if self.type_assets == 'asset_prepayments':
            subtotal = self.price_total
            
        employee_id = self.picking_id.user_id.employee_id or self.picking_id.user_id.employee_ids             
        # TODO: For Testing Only
        # TODO: buat di header, jika ada employee di user maka otomatis 
        if self.picking_id.user_id.name == 'Administrator':
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.picking_id.user_id.id)], limit=1)
        
        if not employee_id:
            raise Warning("Employee not found in user %s" % self.picking_id.user_id.name)
        if not self.asset_category_id:
            raise Warning("Asset Category not found")
            
        vals = {
            'name': self.product_id.name if no == 0 else self.product_id.name + ' - ' + str(no),
            'code': self.name or False,
            'category_id': self.asset_category_id.id,
            'value': subtotal,
            'partner_id': self.picking_id.partner_id.id,
            'company_id': self.picking_id.company_id.id,
            'currency_id': self.product_id.company_currency_id.id,
            'date': self._get_default_date(),
            'purchase_date': self.purchase_order_id.date,
            'product_id': self.product_id.id,
            'company_id': self.picking_id.company_id.id,
            'location_id': self.picking_id.location_dest_id.id,
            # 'invoice_id': self.move_id.id,
            'employee_id': employee_id.id,
            'employee_user_id': self.employee_user_id.id,
            'first_depreciation_manual_date': self._get_default_date(),
        }
    
        changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
        if changed_vals:
            vals.update(changed_vals['value'])
        asset = self.env['account.asset.asset'].create(vals)
        
        if asset.depreciation_line_ids:
            last_date_depreciation = asset.depreciation_line_ids[-1].depreciation_date
            asset.method_end = last_date_depreciation
        if asset.type_assets == 'asset_prepayments':
            asset.note = self.description
        
        if self.is_cip and not self.do_date:
            asset.write({'state': 'CIP'})
        else:
            asset.validate()
        return asset
    
    def create_move_by_asset(self):
        move = {
            'picking_type_id': self.picking_id.picking_type_id.id,
            'origin':self.picking_id.name or '',
            'company_id': self.picking_id.company_id.id,
            'name': self.product_id.default_code or '',
            'product_uom': self.product_id.product_tmpl_id.uom_id.id,
            'product_id':self.product_id.id,
            'product_uom_qty': self.qty,
            'date': datetime.now(),
            'location_id':self.picking_id.picking_type_id.default_location_src_id.id,
            'location_dest_id':self.picking_id.picking_type_id.default_location_dest_id.id,
            'is_create_serial_number':False,
        }
        move_obj = self.env['stock.move'].sudo().create(move)
        self.move_id = move_obj.id
        move_obj.sudo()._action_confirm()
    
    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        additional_params = self._get_tax_base_line_additional_params()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **additional_params,
        )

    def _get_tax_base_line_additional_params(self):
        self.ensure_one()
        return {
            'tax_ids': self.tax_ids,
            'quantity': self.qty,
            'partner_id': self.picking_id.partner_id,
            'currency_id': self.picking_id.company_id.currency_id,
            'price_unit': self._get_price_after_discount(),
        }

    def _get_price_after_discount(self):
        self.ensure_one()
        return self.price - self.discount

     