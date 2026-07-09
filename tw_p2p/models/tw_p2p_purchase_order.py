# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math
import calendar

# 2: import of known third party lib
import xlrd
import base64

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)
# 6: Import of unknown third party lib


class TwP2pPurchaseOrder(models.Model):
    _name = "tw.p2p.purchase.order"
    _description ="P2P Purchase Order"
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    def get_default_datetime(self):
        return datetime.now()
    
    def _get_default_main_dealer_atpm_code(self):
        return self.env['res.company'].get_default_main_dealer_atpm_code()

    def _periode_get(self):
        current_year = str(datetime.now().year)
        obj_periode = self.env['tw.p2p.periode'].search([
                                                        ('name', '=like', current_year + '%'),
                                                        '|', 
                                                        '&', 
                                                        ('start_date', '<=', self._get_default_date()),
                                                        ('end_date', '>=', self._get_default_date()),
                                                        ('active', '=', True)
                                                         ], order='name desc')
        periode = [(periode.name, periode.name) for periode in obj_periode]
        if self.periode_id and self.periode_id not in [p[0] for p in periode]:
            periode.append((self.periode_id, self.periode_id))
        return periode

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not self._periode_get():
            raise Warning("Periode P2P tidak ditemukan, silahkan cek master Periode P2P")
        return res

    def last_day_of_current_month(self):
        today = datetime.today()
        year = today.year
        month = today.month
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day)
    

    # 8: fields
    name = fields.Char(string='Name')
    date = fields.Datetime(string='Date',default=get_default_datetime)

    credit_limit_unit = fields.Float(string='Credit Limit Unit')
    credit_limit_sparepart = fields.Float(string='Credit Limit Sparepart')

    
    periode_id = fields.Selection(_periode_get, string='Periode',store=True)
    state= fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_verification','Waiting for Verification'),
        ('revisi','Revisi'),
        ('confirmed', 'Confirmed'),
        ('cancel','Cancel'),
        ('reject','Reject')      
        ], string='State', readonly=True,default='draft')
    
    is_type_po = fields.Boolean(string='Type P2P')
    description = fields.Char('Description')
    type_name = fields.Char()
    revisi_ke = fields.Integer(string='Revisi Ke',default='0')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # Audit Trail
    waiting_for_verification_uid = fields.Many2one('res.users',string="Waiting Verification by", copy=False)
    waiting_for_verification_date = fields.Datetime('Waiting Verification on', copy=False)
    verification_uid = fields.Many2one('res.users',string="Verification by", copy=False)
    verification_date = fields.Datetime('Verification on', copy=False)
    confirm_uid = fields.Many2one('res.users',string="Confirmed by", copy=False)
    confirm_date = fields.Datetime('Confirmed on', copy=False)
    revisi_uid = fields.Many2one('res.users',string="Revisi by", copy=False)
    revisi_date = fields.Datetime('Revisi on', copy=False)
    rfa_uid = fields.Many2one('res.users',string="RFA by", copy=False)
    rfa_date = fields.Datetime('RFA on', copy=False)
    cancel_uid = fields.Many2one('res.users',string="Cancel by", copy=False)
    cancel_date = fields.Datetime('Cancel on', copy=False)

    # 9: relation fields
    dealer_id = fields.Many2one(
        'res.partner',
        string='Dealer',
        required=True,
        domain=lambda self: [
            ('category_id.name', 'in', ('AHASS', 'Branch')),
            ('id', 'in', self.env['res.company'].sudo().search([
                ('id', 'in', self.env.context.get('allowed_company_ids', [self.env.company.id]))
            ]).mapped('partner_id').ids)
        ]
    )
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True,domain=[('id','=',False)])
    company_id = fields.Many2one("res.company", compute="_compute_dealer_id", store=True) 
    additional_line_ids = fields.One2many('tw.p2p.purchase.order.line','purchase_id')
    sparepart_line_ids = fields.One2many('tw.p2p.purchase.order.line','purchase_id')
    purchase_order_type_id = fields.Many2one('tw.purchase.order.type','Type',required=True, domain="[('division', '=', division),('company_id', 'in', [company_id, False])]")
    approval_ids = fields.One2many('tw.approval.line','transaction_id',string="Table Approval",domain=[('model_id','=',_name)])
    purchase_line_ids = fields.One2many('tw.p2p.purchase.order.line','purchase_id')
    user_id = fields.Many2one('res.users', 'Responsible',default=lambda self: self.env.user)
    purchase_order_id = fields.Many2one('purchase.order',string='Purchase Order', copy=False)
    product_p2p_ids = fields.Many2many(
        comodel_name='product.product',
        relation='tw_p2p_prod_categ_rel', column1='order_id', column2='product_id',
        compute='_compute_product_category_ids',
        string="Product P2P")
    category_fix_order_id = fields.Many2one(
        'tw.p2p.category.fix.order', 
        string='Category Fix Order',
        domain="[('active', '=', True)]"
    )
    
  

    # 10: constraints & sql constraints
    _sql_constraints = [('name_uniq', 'unique(name)', 'Duplicate Name.')]

    @api.constrains('division', 'category_fix_order_id', 'purchase_order_type_id')
    def _check_category_fix_order_required(self):
        """Category Fix Order is required for Sparepart division with Fix type only"""
        for order in self:
            if order.division == 'Sparepart' and order.purchase_order_type_id.name == 'Fix' and not order.category_fix_order_id:
                raise Warning('Category Fix Order wajib diisi untuk divisi Sparepart dengan Type Fix!')

    # 11: compute/depends & on change methods
    @api.onchange('purchase_order_type_id')
    def _product_type_change(self):
        self.type_name = False
        self.additional_line_ids = False
        self.purchase_line_ids = False
        if self.purchase_order_type_id:
            self.type_name = self.purchase_order_type_id.name
    
    @api.onchange('dealer_id')
    def _onchange_supplier_id(self):
        self.supplier_id = False
        self.company_id = False
        if self.dealer_id:
            company_obj = self.env['res.company'].sudo().search([('partner_id', '=', self.dealer_id.id)], limit=1)
            if not company_obj.default_supplier_id:
                raise Warning(f"Pastikan kembali Default supplier pada Branch {self.dealer_id.name} sudah terisi dan pastikan kembali branch pada partner {self.dealer_id.name} sudah terisi")
            
            self.company_id = company_obj.id
            self.supplier_id = company_obj.default_supplier_id.id

    @api.onchange('division')
    def onchange_division(self):
        self.purchase_order_type_id = False
        domain = {}
        if self.division:
            domain['purchase_order_type_id'] = [[('division','=',self.division),'|',('name','=','Fix'),('name','=','Additional')]]
        return {'domain':domain}

    @api.onchange('periode_id', 'date')
    def _onchange_periode_id_date(self):
        if self.periode_id:
            periode_obj = self.env['tw.p2p.periode'].search([('name', '=', self.periode_id)], limit=1)
            if periode_obj:
                self.cek_p2p_periode(periode_obj)

    @api.depends('dealer_id')
    def _compute_dealer_id(self):
        self.company_id = False
        for order in self:
            if order.dealer_id:
                company_obj = self.env['res.company'].sudo().search([('partner_id', '=', order.dealer_id.id)], limit=1)
                order.company_id = company_obj.id
    
    @api.depends('division', 'company_id', 'category_fix_order_id')
    def _compute_product_category_ids(self):
        for order in self:
            if order.division:
                today = datetime.now()
                # Get all parent companies including current company
                company_ids_to_search = order.sudo().company_id.ids
                parent = order.sudo().company_id.parent_id
                while parent:
                    company_ids_to_search.append(parent.id)
                    parent = parent.parent_id
                
                domain = [
                    ('division', '=', order.division),
                    ('start_date', '<=', today.strftime('%Y-%m-%d')),
                    ('end_date', '>=', today.strftime('%Y-%m-%d')),
                    '|',
                    ('company_ids', 'in', company_ids_to_search),
                    ('company_ids', '=', False)
                ]
                # Filter by category_fix_order_id for Sparepart division
                if order.division == 'Sparepart' and order.category_fix_order_id:
                    domain.append(('category_fix_order_id', '=', order.category_fix_order_id.id))
                
                p2p_products = self.env['tw.p2p.product'].search(domain)
                order.product_p2p_ids = [(6, 0, p2p_products.mapped('product_id').ids)]
            else:
                order.product_p2p_ids = [(5, 0, 0)]
    
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            partner_id = self.env['res.partner'].suspend_security().search([('id','in',[vals['dealer_id']])])  
            if not partner_id.code:
                 raise Warning(f'Default Code pada Partner {partner_id.name} tidak ditemukan !')
            vals['name'] = self.env['ir.sequence'].suspend_security().get_sequence_code('P2P',str(partner_id.code))     
            vals['date'] = self.suspend_security()._get_default_date()   
            periode_obj = self.env['tw.p2p.periode'].search([('name','=',vals['periode_id'])], limit=1)
            if not periode_obj:
                raise Warning("Periode P2P tidak ditemukan, silahkan cek master Periode P2P")
            self.cek_p2p_periode(periode_obj)

        purchase_id = super(TwP2pPurchaseOrder, self).create(vals_list)
        return purchase_id    

    
    # TODO: Delete if the transaction requires delete
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning(_('Warning! \nCannot delete records with a state other than draft!'))

        return super(TwP2pPurchaseOrder, self).unlink()
    
    def copy(self):
        self.ensure_one()
        if self.purchase_order_type_id.name != 'Additional':
            raise Warning('Data P2P tidak bisa diduplikasi!')
        
        line_ids = []
        for x in self.additional_line_ids:
            line_ids.append([0, 0, {
                'product_id': x.product_id.id,
                'tent1_prev_qty': x.tent1_prev_qty,
                'fix_qty': x.fix_qty,
                'tent2_prev_qty': x.tent2_prev_qty,
                'type': x.type,
                'tent1_qty': x.tent1_qty,
                'tent2_qty': x.tent2_qty,
            }])
        return super().copy({'additional_line_ids': line_ids})


    # 13: action methods
    def action_recheck(self):
        warning = ""
        msg = ""
        branch_supplier = self.supplier_id.sudo().company_id
        for line in self.sparepart_line_ids :
            qty_in_quant = 0
            qty_in_picking = self.env['stock.picking'].suspend_security()._get_qty_picking(self.dealer_id.company_id,line.purchase_id.division,line.product_id.id)
            if branch_supplier:
                qty_in_quant = self.env['stock.quant'].sudo().get_stock_available(line.product_id.id,branch_supplier.id)
            stock_rfs = qty_in_quant-qty_in_picking   
            if stock_rfs < line.fix_qty:
                if stock_rfs <= 0:
                    msg = 'Qty Not Available'
                else:
                    msg = 'Qty Available %s' %stock_rfs
                warning += "- %s %s \r\n" % (line.product_id.name,msg)

        if warning != "" :
            raise Warning("Stok Available tidak mencukupi untuk Barang-barang dibawah ini:\r\n %s " % warning)
    
    def action_reject_by_ahm(self):
        self.state = 'reject'
        self.copy()

    def action_generate_line(self):
        # * Check Line
        if self.purchase_line_ids:
            raise Warning('Product Line telah terbentuk !')
        product = []
        rekap_periode=[]
        branch_supplier = self.supplier_id.sudo().company_id
        categ_ids = self.env['product.category'].suspend_security().get_child_ids(self.division)
        date = self.date
        
        # Get all parent companies including current company
        company_ids_to_search = self.company_id.ids
        parent = self.company_id.parent_id
        while parent:
            company_ids_to_search.append(parent.id)
            parent = parent.parent_id
        
        rekap_product_domain = [
            ('categ_id', 'in', categ_ids),
            ('start_date', '<=', str(date.date())),
            ('end_date', '>=', str(date.date())),
            '|',
            ('company_ids', 'in', company_ids_to_search),
            ('company_ids', '=', False)
        ]
        # Filter by category_fix_order_id for Sparepart division
        if self.division == 'Sparepart' and self.category_fix_order_id:
            rekap_product_domain.append(('category_fix_order_id', '=', self.category_fix_order_id.id))
        
        rekap_product = self.env['tw.p2p.product'].suspend_security().search(rekap_product_domain)
        for x in rekap_product:
            product.append(x.product_id)
        
        # Validate duplicate products
        self._validate_duplicate_products(product)
         
        product_line = self.env['tw.p2p.purchase.order.line']
        
        if self.periode_id[-2:] == '01' :
            periode_prev = int(self.periode_id[:4]) - 1
            obj_periode = self.env['tw.p2p.periode'].search([
                                                              ('name','like',str(periode_prev))
                                                              ])
            for x in obj_periode :
                rekap_periode.append(x.name)
            prev_periode = max(rekap_periode)  
        else :
            prev_periode = int(self.periode_id) - 1
        prev_purchase = self.search([
                                    ('periode_id','=',prev_periode),
                                    ('supplier_id','=',self.supplier_id.id),
                                    ('division','=',self.division),
                                    ('state','=','confirmed'),
                                    ('purchase_order_type_id','=',self.purchase_order_type_id.id)
                                     ],limit=1)
        if prev_purchase :
            product_rekap = {}
            for line in product : 
                qty_in_quant = qty_in_lot = 0
                product_get = product_line.search([
                                                   ('purchase_id','=',prev_purchase.id),
                                                   ('product_id','=',line.id)
                                                   ])
                if product_get :
                    if self.division=='Unit' :
                        qty_in_picking = self.env['stock.picking']._get_qty_picking(branch_supplier,self.division,product_get.product_id.id)
                        if branch_supplier:
                            qty_in_lot = self.env['stock.quant'].get_stock_available(product_get.product_id.id,branch_supplier)
                        qty=qty_in_lot-qty_in_picking
                       
                    elif self.division=='Sparepart':
                         qty_in_picking = self.env['stock.picking']._get_qty_picking(branch_supplier,self.division,product_get.product_id.id)
                         if branch_supplier:
                            qty_in_lot = self.env['stock.quant'].get_stock_available(product_get.product_id.id,branch_supplier)
                         qty=qty_in_quant-qty_in_picking

                    product_line_vals = {
                                            'product_id': product_get.product_id.id,
                                            'purchase_id' :self.id,
                                            'qty_available' :qty,
                                            'fix_qty':product_get.tent1_qty,
                                            'tent1_qty': product_get.tent2_qty,
                                            'tent1_prev_qty' :product_get.tent1_qty,
                                            'tent2_prev_qty' : product_get.tent2_qty,                            
                                          }
                    self.env['tw.p2p.purchase.order.line'].create(product_line_vals)    
                else :
                    product_line_vals = {
                                            'product_id': line.id,
                                            'purchase_id' :self.id,         
                                            'tent1_prev_qty' :-1,
                                            'tent2_prev_qty' : -1, 
                                            'qty_available' : -1,                                                                                        
                                          }
                    self.env['tw.p2p.purchase.order.line'].create(product_line_vals)                     
        if not prev_purchase :
            if not product :
                raise Warning('Silahkan isi product dalam master P2P product terlebih dahulu !')
            for line in product : 
                qty_in_quant = qty_in_lot = 0
                if self.division =='Unit' :
                        qty_in_picking = self.env['stock.picking']._get_qty_picking(branch_supplier,self.division,line.id)                        
                        if branch_supplier:
                            qty_in_lot = self.env['stock.quant'].get_stock_available(line.id,branch_supplier.id)
                        qty=qty_in_lot-qty_in_picking
                        
                elif self.division =='Sparepart':
                        qty_in_picking = self.env['stock.picking']._get_qty_picking(branch_supplier,self.division,line.id)
                        if branch_supplier:
                            qty_in_lot = self.env['stock.quant'].get_stock_available(line.id,branch_supplier.id)
                        qty=qty_in_quant-qty_in_picking
                
                product_line_vals = {
                                        'product_id': line.id,
                                        'purchase_id' :self.id,  
                                        'qty_available' :qty,  
                                        'tent1_prev_qty' :-1,
                                        'tent2_prev_qty' : -1,                                     
                                      }
                self.env['tw.p2p.purchase.order.line'].create(product_line_vals)    
    
    def action_create_purchase_order(self):
        periode = self.env['tw.p2p.periode'].sudo().search([('name','=',self.periode_id)])         
        start_date = periode.periode_start_date
        end_date = periode.periode_end_date
        product_pricelist = self.env['product.pricelist']
        branch_requester = self.env['res.company'].suspend_security().search([('partner_id','=',self.dealer_id.id)])
        picking_type = self.env['stock.picking.type'].get_picking_type('incoming', branch_requester.id, self.division,False)
        total_qty = 0.0   
        order_line_vals = []
        if self.type_name == 'Fix'   :                                          
            for line in self.purchase_line_ids :
                  total_qty += line.fix_qty 
            if total_qty < 1 :
                    raise Warning("Total Fix Qty harus lebih besar dari 0")
        elif self.type_name == 'Additional'   :                                          
            for line in self.additional_line_ids :
                  total_qty += line.fix_qty 
            if total_qty < 1 :
                    raise Warning("Total Fix Qty harus lebih besar dari 0")
                            
        if self.supplier_id :
            # cek Purchase Order
            po_obj = self.env['purchase.order'].sudo().search([('origin','=',self.name)])
            if po_obj:
                return po_obj
            last_day = self.last_day_of_current_month()            
            if self.type_name == 'Fix' :
                for line in self.purchase_line_ids :
                    if line.fix_qty > 0 :    
                        uom_id = False
                        product_uom_po_id = line.product_id.uom_po_id.id
                        if not uom_id:
                            uom_id = product_uom_po_id                
                        taxes = [(6, 0, line.product_id.supplier_taxes_id.ids)] if line.product_id.supplier_taxes_id else False
                        order_line_vals.append([0,0,{                  
                            'product_id': line.product_id.id,
                            'product_qty': line.fix_qty,
                            'product_uom' : uom_id,                            
                            'name':line.product_id.description if line.product_id.description else '',
                        }])
            elif self.type_name == 'Additional' :
                for line in self.additional_line_ids :
                    if line.fix_qty > 0 :    
                        uom_id = False
                        product_uom_po_id = line.product_id.uom_po_id.id
                        if not uom_id:
                            uom_id = product_uom_po_id                
                        
                        order_line_vals.append([0,0,{                                           
                            'product_id': line.product_id.id,
                            'product_qty': line.fix_qty,
                            'product_uom' : uom_id,
                            'name':line.product_id.description if line.product_id.description else line.product_id.name,
                        }])
            
            order_vals = {
                'company_id': branch_requester.id,
                'origin':self.name,
                'division': self.division,
                'partner_id': self.supplier_id.id,
                'date_order': last_day,
                'purchase_order_type_id': self.purchase_order_type_id.id,
                'state': 'draft',
                'picking_type_id' :picking_type.id,
                'company_id': branch_requester.id,
                'user_id': self._uid,
                'order_line': order_line_vals,
                'start_date':start_date,
                'end_date':end_date            
            }
            order_id = self.env['purchase.order'].suspend_security().with_company(branch_requester.id).create(order_vals)
            self.purchase_order_id = order_id.id
            # order_id.action_confirm()
            order_id.sudo().button_confirm()
            return order_id
    

    def action_view_po(self,context=None):  
        po_ids = self.env['purchase.order'].suspend_security().search([('origin','=',self.name)]).id
        return {
            'name': 'Purchase Order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': po_ids,
            }
    
    def action_to_draft(self):
        self.write({'state':'draft',
                    'write_uid': self._uid,
                    'write_date' : datetime.now()})
                
    

    def action_export_import_wizard(self):
        view_id = self.env.ref('tw_p2p.tw_p2p_purchase_order_export_import_wizard_form_view').id
        return {
            'name': ('Export / Import'),
            'res_model': 'tw.p2p.export.import',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(view_id, 'form')],
            'target': 'new',
            'view_mode': 'form',
            'context': {
                 'readonly_by_pass': True,
                 'default_purchase_order_type_id': self.purchase_order_type_id.id,
                 'default_purchase_order_id': self.id

            }
        }
    
    def action_verification(self):
        self._verification_additional()
        if self.state in ('confirmed'):
            raise Warning(f'State sudah {self.state}')
        
        return self.write({
            'state': 'waiting_for_verification',
            'waiting_for_verification_uid': self._uid,
            'waiting_for_verification_date': datetime.now()

        })
    
    def action_revisi(self):
        for p2p in self:
            if p2p.state in ('revisi','confirmed'):
                raise Warning(f'State sudah {p2p._get_state_value()}')
        
            p2p.revisi_ke = p2p.revisi_ke + 1

            p2p.write({
                'state': 'revisi',
                'revisi_uid': self._uid,
                'revisi_date': datetime.now()

            })
    
    def action_print_document(self):
        if self.state != 'confirmed':
            raise Warning(f'Print dapat dilakukan setelah State sudah Confirmed.')

        self.ensure_one()
        return self.env.ref('tw_p2p.action_report_p2p_purchase_order').report_action(self.id)
    
    # def action_p2p_purchase_order_report(self):
    #     if self.state != 'confirmed':
    #         raise Warning(f'Print dapat dilakukan setelah State sudah Confirmed.')

    #     self.ensure_one()
    #     return self.env.ref('tw_p2p.action_report_p2p_purchase_order').report_action(self.id)

    # 14: private methods    

    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state
    
    
    def validate_order(self):
        ids_product = []
        for line in self.additional_line_ids :
            ids_product.append(line.product_id.id)
        if ids_product :
            ids_product.sort(reverse=False)
            id_product_before = 0
            for id in ids_product :
                if id_product_before == id :
                    raise Warning('Tidak boleh ada Product yg sama dalam satu transaksi !')
                id_product_before = id
            
        if not self.purchase_line_ids and self.type_name == 'Fix':
            raise Warning('Silahkan Generate data terlebih dahulu !')
        
        if not self.additional_line_ids and self.type_name == 'Additional':
            raise Warning('Silahkan isi detil terlebih dahulu !')                 
                
        supplier_id = self.supplier_id
            
        periode_obj = self.env['tw.p2p.periode'].search([('name','=',self.periode_id)], limit=1)
        if not periode_obj:
            raise Warning("Periode tidak ditemukan")

        if self.type_name == 'Fix' :    
            self.cek_data()
        self.cek_p2p_type_color()
        total_qty = 0.0   
        if self.type_name == 'Fix'   :                                          
            for line in self.purchase_line_ids :
                  total_qty += line.fix_qty 
            if total_qty < 1 :
                    raise Warning("Total Fix Qty harus lebih besar dari 0")
        elif self.type_name == 'Additional'   :                                          
            for line in self.additional_line_ids :
                  total_qty += line.fix_qty 
            if total_qty < 1 :
                    raise Warning("Total Fix Qty harus lebih besar dari 0")
                            
        self.cek_p2p_config(supplier_id)
        self.cek_p2p_periode(periode_obj)
    
    
    def cancel_order(self):
        if self.state not in ('draft'):
            raise Warning(f'Transaksi ini telah dibatalkan. Silakan refresh halaman ini!')
        self.write({'state':'cancel',
                    'cancel_uid': self._uid, 
                    'cancel_date' : datetime.now()}) 
        
    
    def cek_data(self):
        #cek data                
        data_search = self.search([
                                   ('id','!=',self.id),
                                   ('supplier_id','=',self.supplier_id.id),
                                   ('periode_id','=',self.periode_id),
                                   ('purchase_order_type_id','=',self.purchase_order_type_id.id),
                                   '|','|',
                                   ('state','=','waiting_for_approval'),
                                   ('state','=','confirmed'),
                                   ('state','=','approved')
                                   ])
        if data_search :
            raise Warning('Transaksi pernah dibuat dengan nomor Transaksi %s' %(data_search[0].name))
           
    
    def cek_p2p_type_color(self):
        #cek product
        date = self.date        
        for x in self.purchase_line_ids:
            products = self.env['tw.p2p.product'].suspend_security().search([('product_id', '=', x.product_id.id)])
            attr_string = ", ".join(["%s: %s" % (attr_value.attribute_id.name, attr_value.name) for attr_value in x.product_id.product_template_attribute_value_ids])
            attr_string = "[%s]" % attr_string if attr_string else "[No Attributes]"

            if not products:
                raise Warning("Product %s [%s] dengan attribute %s tidak ditemukan!" % (x.product_id.name, x.product_id.default_code, attr_string))

            # Check if at least one product is within valid date range
            has_valid_product = False
            for product in products:
                if product.start_date <= date.date() <= product.end_date:
                    has_valid_product = True
                    break
            
            if not has_valid_product:
                raise Warning("Product %s [%s] dengan attribute %s sudah tidak aktif!" % (x.product_id.name, x.product_id.default_code, attr_string))
      
    
    def cek_p2p_config(self,supplier_id):
        #cek type color
        p2p_config = self.env['tw.p2p.config'].search([('supplier_id','=',supplier_id.id)])
        if not p2p_config :
                raise Warning("Supplier %s tidak ditemukan di Master P2P Config"%(supplier_id.name))
            
    def cek_p2p_periode(self, periode):
        #cek periode (periode arg is already a recordset)
        date = self.date or self.suspend_security()._get_default_date()           
        if str(date.date()) < str(periode.start_date) or str(date.date()) > str(periode.end_date):
            raise Warning("Tanggal tidak termasuk dalam periode %s, mohon cek kembali Master P2P Periode" % (periode.name))
    
    
    def confirm_order(self):    
        if self.purchase_order_id and self.purchase_order_id.state not in ('cancel'):
            raise Warning(f'Transaksi P2P ini telah memiliki PO dengan nomor {self.purchase_order_id.name}')
        main_dealer_code = self.env['res.company'].get_default_main_dealer_code()
        purchase_order_obj = False
        vals_confirm = {
            'state': 'confirmed',
            'date': self._get_default_date(),
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_date()
        }
        branch_sender = self.env['res.company'].suspend_security().search([('partner_id','=',self.supplier_id.id)])
        # Jika order dari main dealer atau supplier bukan branch, maka membentuk PO
        if (self.dealer_id.company_id and self.dealer_id.company_id.code == main_dealer_code) or not branch_sender:
            purchase_order_obj = self.action_create_purchase_order()
            vals_confirm['purchase_order_id'] = purchase_order_obj.id
            self.is_type_po = True
        
        return self.write(vals_confirm)
                            
    def _get_price_unit(self, pricelist, product):
        if not pricelist:
             pricelist._get_applicable_rules(product,date)
        price_unit = pricelist.with_company(self.company_id.id)._price_get(product,1).get(pricelist.id,product.standard_price)
        return price_unit

    def _get_pricelist(self,branch,division):
        return self.env['tw.branch.setting']._get_pricelist_purchase(branch, division)
    
    def _validate_duplicate_products(self, products):
        """Validate that there are no duplicate products in the list"""
        seen_products = {}
        duplicates = []
        for prod in products:
            if prod.id in seen_products:
                duplicates.append(f"{prod.name} [{prod.default_code}]")
            else:
                seen_products[prod.id] = prod.name
        
        if duplicates:
            raise Warning("Ditemukan produk duplikat di Master P2P Product:\n• " + "\n• ".join(duplicates[:10]) + 
                         (f"\n... dan {len(duplicates) - 10} lainnya" if len(duplicates) > 10 else ""))

    def _verification_additional(self):
        if not self.additional_line_ids and self.purchase_order_type_id.name == 'Additional':
            raise Warning("Empty order lines are not allowed. Please remove any blank lines or fill in all required fields before saving this Purchase Order.")
