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


class twP2pPuchaseOrderLine(models.Model):
    _name = "tw.p2p.purchase.order.line"
    _description ="P2P Purchase Order Line"
    _rec_name = 'product_id'

    # 7: defaults methods

    # 8: fields
    fix_qty = fields.Integer(string='Fix Qty',default=1)
    qty_available = fields.Integer(string='Qty Available (Prev)')
    tent1_qty = fields.Integer(string='Tent 1 Qty')
    tent2_qty = fields.Integer(string='Tent 2 Qty')
    tent1_prev_qty = fields.Integer(string='Tent 1 Qty(Prev)')
    tent2_prev_qty = fields.Integer(string='Tent 2 Qty(Prev)')
    active = fields.Boolean(default=True)  
    type = fields.Char(related="purchase_id.type_name",string="Type")     
    

    # 9: relation fields
    purchase_id = fields.Many2one('tw.p2p.purchase.order',string='Purchase')
    product_id = fields.Many2one('product.product',string='Product')

    _sql_constraints = [
        ('product_id_unique', 'unique(purchase_id,product_id)', 'Tidak boleh ada produk yang sama di dalam satu P2P !')
    ]

    @api.onchange('product_id')
    def onchange_product(self):
        if not self.purchase_id.supplier_id:
            raise Warning('Silahkan isi Supplier terlebih dahulu !')
        if self.purchase_id.type_name == 'Additional':
            date = str(self.purchase_id.date)
            division = self.env.context.get('division', False) or self.purchase_id.division
            company = self.purchase_id.sudo().company_id
            
            # Get all parent companies including current company
            company_ids_to_search = company.ids
            parent = company.parent_id
            while parent:
                company_ids_to_search.append(parent.id)
                parent = parent.parent_id
            
            # Use ORM instead of raw SQL for security and company filtering
            domain = [
                ('division', '=', division),
                ('start_date', '<=', date),
                ('end_date', '>=', date),
                '|',
                ('company_ids', 'in', company_ids_to_search),
                ('company_ids', '=', False)
            ]
            p2p_products = self.env['tw.p2p.product'].search(domain)
            product_ids = p2p_products.mapped('product_id').ids
            
            branch_supplier = self.purchase_id.supplier_id.sudo().company_id 
            qty_in_quant = qty_in_lot = 0
            if self.purchase_id.division == 'Unit' and self.product_id:
                qty_in_picking = self.env['stock.picking']._get_qty_picking(branch_supplier, self.purchase_id.division, self.product_id.id)
                if branch_supplier:
                    qty_in_lot = self.env['stock.quant'].get_stock_available(self.product_id.id, branch_supplier.id)
                self.qty_available = qty_in_lot - qty_in_picking
            elif self.purchase_id.division == 'Sparepart' and self.product_id:
                qty_in_picking = self.env['stock.picking']._get_qty_picking(branch_supplier, self.purchase_id.division, self.product_id.id)
                if branch_supplier:
                    qty_in_quant = self.env['stock.quant'].sudo().get_stock_available(self.product_id.id, branch_supplier.id)
                self.qty_available = qty_in_quant - qty_in_picking

    @api.onchange('fix_qty')
    def onchange_fix_qty(self):
        if self.purchase_id.type_name == 'Fix' and self.fix_qty < 0 :
            self.fix_qty = 0        
            raise Warning("Nilai Fix Qty tidak boleh kurang dari nol")
        else :
            if self.fix_qty < 0 :
                raise Warning("Nilai Fix Qty tidak boleh kurang dari nol")
                
            if self.purchase_id.type_name == 'Fix' and self.fix_qty and self.tent1_prev_qty >= 0 :
                prev_qty = self.tent1_prev_qty
                fix_qty = self.fix_qty                        
                #cek P2P config based on branch or branch destination
                supplier_id = self.purchase_id.supplier_id
                    
                p2p_config = self.env['tw.p2p.config'].search([
                                                                ('supplier_id','=',supplier_id.id)
                                                                ])
                if not p2p_config :
                    raise Warning("Mohon isi P2P Config untuk supplier %s terlebih dahulu !" %(supplier_id.name))
 
                config = p2p_config.tentative_1
                ceil = math.ceil(prev_qty * (100.0 + config)/100)
                floor = math.floor(prev_qty * (100.0 - config)/100)
                  
                if fix_qty > ceil or fix_qty < floor :                      
                        self.fix_qty = self.tent1_prev_qty
                        raise Warning("Nilai Fix Qty tidak boleh melebihi batas min/max %s%s !" %(config,'%'))


    @api.onchange('tent1_qty')
    def onchange_tent1_qty(self):
        if self.purchase_id.type_name == 'Fix' and self.tent1_qty < 0 :
            self.tent1_qty = 0        
            raise Warning("Nilai Tentative 1 Qty tidak boleh kurang dari nol")                  
        else :        
            if self.purchase_id.type_name == 'Fix' and self.tent1_qty and self.tent2_prev_qty >= 0 :
                prev_qty = self.tent2_prev_qty
                fix_qty = self.tent1_qty
   
                #cek P2P config based on branch or branch destination
                supplier_id = self.purchase_id.supplier_id
                    
                p2p_config = self.env['tw.p2p.config'].search([
                                                                ('supplier_id','=',supplier_id.id)
                                                                ])
                if not p2p_config :
                    raise Warning("Mohon isi P2P Config untuk %s terlebih dahulu !" %(supplier_id.name))    
                
                config = p2p_config.tentative_2
                ceil = math.ceil(prev_qty * (100.0 + config)/100)
                floor = math.floor(prev_qty * (100.0 - config)/100) 
    
                if fix_qty > ceil or fix_qty < floor :
                        self.tent1_qty = self.tent2_prev_qty
                        raise Warning("Nilai Fix Qty tidak boleh melebihi batas min/max %s%s !" %(config,'%'))                      
            
    @api.onchange('tent2_qty')
    def onchange_tent2_qty(self):  
        if self.purchase_id.type_name == 'Fix' and self.tent2_qty < 0 :
            self.tent2_qty = 0                        
            raise Warning("Nilai Tentative 2 Qty tidak boleh kurang dari nol")                  


    # override method
    @api.model_create_multi
    def create(self, vals_list):
        for record in vals_list:
            if 'fix_qty' in record:
                fix_qty = record.get('fix_qty', 0) or 0
                if fix_qty <= 0:
                    raise Warning("Fix Quantity in Order Line cannot be less than or equal to 0.")
        return super().create(vals_list)

    def write(self, vals):
        if 'fix_qty' in vals:
            fix_qty = vals['fix_qty']
            if fix_qty <= 0:
                raise Warning("Fix Quantity in Order Line cannot be less than or equal to 0.")
        return super().write(vals)