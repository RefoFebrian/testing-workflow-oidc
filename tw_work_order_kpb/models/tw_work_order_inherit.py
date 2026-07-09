# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"
    # 7: defaults methods

    # 8: fields
    book_code = fields.Char(string='Kode Buku')
    book_number = fields.Char(string='Nomor Buku')
    is_event_kpb = fields.Boolean(string='KPB Event State', readonly=True, copy=False, help="It indicates that this Work Order got an exception on KPB Checking")
    kpb_ke = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    ], string='KPB Ke')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('type','company_id')
    def onchange_type_new(self):
        self.kpb_ke = False 
        return super().onchange_type_new()
    
    def _prepare_customer_stnk_id(self):
        if not self._check_payment_term_id_fields():
            return
        if self.customer_stnk_id:
            if self.type_id.value == 'REG':
                self.payment_term_id = self.customer_stnk_id.property_payment_term_id.id
            elif self.type_id.value in self._prepare_type_onchange_customer_stnk_id():
                branch = self.company_id
                if branch and branch.default_supplier_id:
                    self.payment_term_id = branch.default_supplier_id.property_payment_term_id.id
                else:
                    self.payment_term_id = 1
        else:
            self.payment_term_id = False
    @api.onchange('book_code')
    def book_code_onchange(self):
        if self.book_code:
            self.book_code = self.book_code.replace(' ', '').upper()

    @api.onchange('book_number')
    def book_number_onchange(self):
        if self.book_number:
            self.book_number = self.book_number.replace(' ', '').upper()

    # 12: override methods
    def _override_combined_tax(self,vals):
        if vals.get('type') in self._prepare_type_wo(['KPB']):
            if 'combined_tax' in self._fields:
                vals['combined_tax'] = True
    
    def _override_check_type_service(self,type_service,wo_obj,driver_obj):
        payment_term_id = False
        if type_service == 'REG':
            payment_term_id = driver_obj.property_payment_term_id.id
        elif type_service in self._prepare_type_wo(['KPB']):
            if wo_obj._name == 'tw.work.order':
                branch_obj = self.env['res.company'].browse(wo_obj.company_id.id)
                payment_term_id = branch_obj.default_supplier_id.property_payment_term_id.id
        return payment_term_id if payment_term_id else 1
    
    def _get_combined_tax(self,vals):
        work_order_type_obj = self.env['tw.selection'].browse(vals.get('type_id'))
        if work_order_type_obj:
            if work_order_type_obj.value in self._prepare_type_wo(['KPB']):
                if 'combined_tax' in self._fields:
                    vals['combined_tax'] = True
            elif work_order_type_obj.value in ('REG', 'WAR'):
                if 'combined_tax' in self._fields:
                    vals['combined_tax'] = False

    # Prepare
    def _prepare_type_wo(self,wo_type=[]):
        prepare = super()._prepare_type_wo(wo_type)
        wo_type.append('KPB')
        return prepare
    
    def _prepare_rfa(self,obj_po):
        if obj_po.type_id.value == 'KPB':
            duplicate_wo = self.search([
                ('id', '!=', obj_po.id),
                ('type_id.value', '=', 'KPB'),
                ('kpb_ke', '=', obj_po.kpb_ke),
                ('lot_id', '=', obj_po.lot_id.id),
                ('state', 'not in', ('draft', 'unused', 'cancel'))
            ], limit=1)
            if duplicate_wo:
                raise ValidationError(f"WO KPB {obj_po.kpb_ke} untuk nosin {obj_po.lot_id.name} sudah dibentuk di WO {duplicate_wo.name}!")
        prepare = super()._prepare_rfa(obj_po)
        return prepare
    
    def _prepare_vals_before_create(self,vals):
        prepare = super()._prepare_vals_before_create(vals)
        is_event = vals.get('is_event_kpb', False)

        workorder_type_obj = self.env['tw.selection'].browse(vals.get('claim_type_id'))
        self._get_wo(workorder_type_obj.value, vals.get('date'), vals.get('purchase_date'),
            vals.get('lot_id'), vals.get('kpb_ke'), vals.get('km'), is_event)  
        self._override_combined_tax(vals) 
        return prepare
    
    def _prepare_type_onchange_customer_stnk_id(self,wo_type=[]):
        change_type = super()._prepare_type_onchange_customer_stnk_id(wo_type)        
        if 'KPB' not in wo_type:
            wo_type.append('KPB')
        return change_type
    
    def _get_partner_id(self, type, partner_id, company_id):
        if type in self._prepare_type_wo(['KPB']):
            branch = self.env['res.company'].browse(company_id)
            if not branch.default_supplier_id:
                raise ValidationError(_('Principle di Branch Belum di Setting'))
            return branch.default_supplier_id.id
        return partner_id
    
    def _get_wo(self, type, date, purchase_date, lot_id, kpb_ke, km, is_event_kpb):
        if type == 'KPB':
            tanggal_wo_format = fields.Date.from_string(date)
            purchase_date_format = fields.Date.from_string(purchase_date)
            pengurangan_hari = abs((tanggal_wo_format - purchase_date_format).days)
            
            lot = self.env['stock.lot'].browse(lot_id)
            obj_engine = self.env['tw.kpb.expired']
            vit = obj_engine.search([('name', '=', lot.name[:4]), ('service', '=', kpb_ke)], limit=1)
            
            if not vit:
                raise ValidationError(_('Master KPB %s untuk Kode Engine %s tidak ditemukan di "Master KPB Expired"' % (kpb_ke, lot.name[:4])))
            data = vit
            
            if not is_event_kpb:
                if km > data.km:
                    raise ValidationError(_('Kilometer telah lewat batas KPB'))
                elif km == 0:
                    raise ValidationError(_('Kilometer tidak boleh nol'))
                if pengurangan_hari > data.hari:
                    raise ValidationError(_('Tanggal KPB sudah lewat batas KPB'))
        elif km <= 0:
            raise ValidationError(_('Kilometer tidak boleh nol atau negatif.'))
        return True
