# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
import requests
import json

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
import logging
_logger = logging.getLogger(__name__)

# 5: local imports

# 6: Import of unknown third party lib

class TWB2BApiEv(models.Model):
    _name = "tw.b2b.api.ev"
    _description = "TW B2B API EV"
    _order = "id DESC"
    _rec_name = 'ship_list_number'
    
    # 7: defaults methods

    # 8: fields
    ship_list_number = fields.Char(string='Nomor SL')
    ship_list_date = fields.Date(string='Tanggal SL')
    md_code = fields.Char(string='Kode MD')
    voucher_acc = fields.Char(string='Voucher Acc')
    packing_number = fields.Char(string='Nomor Packing')
    jenis_acc = fields.Char(string='Jenis Acc')
    state = fields.Selection([
        ('draft','Draft'),
        ('waiting','Waiting Availability'),
        ('assigned','Ready to transfer'),
        ('duplicate','Duplicate'),
        ('error','Error'),
        ('done','Done'),
    ], string='State', default='draft')
    message = fields.Text(string='Message')
    hit_api_date = fields.Datetime('Tanggal HIT API')

    # 9: relation fields
    picking_id = fields.Many2one('stock.picking', string='Picking', help='Related Picking')
    company_id = fields.Many2one('res.company', string='Branch', default=lambda self: self.env.company)
    line_ids = fields.One2many('tw.b2b.api.ev.line', 'b2b_api_ev_id', string='Line')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_process(self):
        self._process_single_record({
            'ship_list_number': self.ship_list_number,
            'packing_number': self.packing_number,
            'ship_list_date': self.ship_list_date,
            'voucher_acc': self.voucher_acc,
            'jenis_acc': self.jenis_acc,
            'line_ids': self.line_ids
        })
        self.suspend_security().write({'state': 'waiting'})
    
    def action_open_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_stock.tw_stock_picking_inherit_form_view').id,
            'res_id': self.picking_id.id
        }

    # 14: private methods
    def _get_branch_and_picking_type(self):
        """Helper method to get branch and picking type objects"""
        branch_obj = self.env['res.company'].suspend_security().get_default_main_dealer()
        picking_type_obj = branch_obj.warehouse_id.in_type_id
        return branch_obj, picking_type_obj

    def _get_division(self, jenis_acc):
        """Helper method to determine division based on jenis_acc"""
        return 'Extras' if jenis_acc == 'OEM' else 'Sparepart'

    def _create_product_if_not_exists(self, part_code, part_desc, type_acc, jenis_acc):
        """Helper method to create product if it doesn't exist"""
        product_tmpl_obj = self.env['product.template'].suspend_security().search([('default_code', '=', part_code)])
        if product_tmpl_obj:
            return product_tmpl_obj
        
        domain_categ = [('name', '=', type_acc), ('parent_id.name', '=', 'Sparepart')]
        if jenis_acc == 'OEM':
            domain_categ = [('name', '=', type_acc), ('parent_id.name', '=', 'Extras')]
        
        product_category_obj = self.env['product.category'].suspend_security().search(domain_categ)
        if not product_category_obj:
            raise Warning(f"Category {type_acc} not found!")
        
        vals_product = {
            'name': part_desc,
            'default_code': part_code,
            'categ_id': product_category_obj.id,
            'sale_ok': True,
            'purchase_ok': True,
            'is_storable': True,
            'lot_valuated': True,
            'tracking': 'serial',
            'type': 'consu',
        }
        return self.env['product.template'].sudo().create(vals_product)

    def _create_lot(self, serial_number, branch_obj, product_obj, acc_data, picking_type_obj):
        """Helper method to create stock lot if it doesn't exist"""
        lot_obj = self.env['stock.lot'].suspend_security().search([('name', '=', serial_number)], limit=1)
        if lot_obj:
            return lot_obj
        
        vals_lot = {
            'name': serial_number,
            'company_id': branch_obj.id,
            'division': acc_data.get('division'),
            'product_id': product_obj.id,
            'supplier_id': branch_obj.default_supplier_id.id,
            'location_id': picking_type_obj.default_location_src_id.id,
            'ship_list_number': acc_data.get('ship_list_number'),
            'ship_list_date': acc_data.get('ship_list_date'),
            'state': 'intransit',
            'box_number': acc_data.get('box_number'),
            'packing_number': acc_data.get('packing_number'),
            'carton_number': acc_data.get('carton_number'),
            'jenis_acc': acc_data.get('jenis_acc'),
            'voucher_acc': acc_data.get('voucher_acc'),
            'category_acc': acc_data.get('type_acc')
        }
        return self.env['stock.lot'].sudo().create(vals_lot)

    def _process_single_record(self, record_data):
        """Process a single record data"""
        branch_obj, picking_type_obj = self._get_branch_and_picking_type()
        if not branch_obj or not picking_type_obj:
            raise Warning(f"Branch or Picking Type not found!")
        
        division = self._get_division(record_data.get('jenis_acc'))
        
        for line in record_data.get('line_ids'):
            acc_data = {
                'ship_list_number': record_data.get('ship_list_number'),
                'packing_number': record_data.get('packing_number'),
                'ship_list_date': record_data.get('ship_list_date'),
                'voucher_acc': record_data.get('voucher_acc'),
                'jenis_acc': record_data.get('jenis_acc'),
                'division': division,
                'box_number': line.box_number,
                'carton_number': line.carton_number,
                'type_acc': line.type_acc
            }
            
            product_tmpl_obj = self._create_product_if_not_exists(
                line.part_code,
                line.part_desc,
                line.type_acc,
                record_data.get('jenis_acc')
            )
            
            product_obj = self.env['product.product'].suspend_security().search([
                ('product_tmpl_id', '=', product_tmpl_obj.id)
            ], limit=1)
            
            self._create_lot(line.serial_number, branch_obj, product_obj, acc_data, picking_type_obj)

    def scheduler_create_lot_ev(self, limit=50):
        """Scheduler method to process multiple records"""
        try:
            data_obj = self.suspend_security().search([('state', '=', 'draft')],limit=limit)
            if not data_obj:
                obj_ev_err = self.suspend_security().search([('state', '=', 'error')])
                for rec in obj_ev_err:
                    rec.sudo().write({'state': 'draft'})
                return True
            
            for data in data_obj:
                data_dict = {
                    'ship_list_number': data.ship_list_number,
                    'packing_number': data.packing_number,
                    'ship_list_date': data.ship_list_date,
                    'voucher_acc': data.voucher_acc,
                    'jenis_acc': data.jenis_acc,
                    'line_ids': data.line_ids
                }
                self._process_single_record(data_dict)
                data.write({'state': 'waiting'})
            
        except Exception as e:
            message = f"Error in scheduler: {str(e)}"
            raise Warning(message)

