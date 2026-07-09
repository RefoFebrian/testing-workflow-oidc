# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _name = "tw.work.order"
    _inherit = ["tw.work.order","tw.approval.mixin"]

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # Selection
    state = fields.Selection(selection_add=[
        ('draft',),
        ('sent',),
        ('waiting_for_approval','Waiting Approval'),
        ('approved', 'Approved'),
        ('confirmed',),
        ('sale',),
        ('except_picking',),
        ('except_invoice',),
        ('done',),
        ('unused',),
        ('cancel',),
        ('rejected', 'Rejected'),
        ])
    
    approval_discount = fields.Float(string='Approval Discount', compute='_compute_approval_discount')

    # Audit Trail
    wfa_uid = fields.Many2one('res.users', string='Waiting Approval by')
    wfa_date = fields.Datetime(string='Waiting Approval on')
    approved_uid = fields.Many2one('res.users', string='Approved by')
    approved_date = fields.Datetime(string='Approved on')
    rejected_uid = fields.Many2one('res.users', string='Rejected by')
    rejected_date = fields.Datetime(string='Rejected on')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('state')
    def _compute_is_other_module_installed(self):
        if self.env['ir.module.module'].search([('name', '=', 'tw_work_order_clocking')], limit=1).state == 'installed':
            for rec in self:
                rec.is_other_module_installed = True
        else:
            for rec in self:
                rec.is_other_module_installed = False
    
    @api.depends('order_line.discount')
    def _compute_approval_discount(self):
        for rec in self:
            rec.approval_discount = rec.get_amount_discount()
    
    @api.depends('state')
    def _compute_is_invisible_action_by_state(self):
        # Approval
        state = 'approved' 
        # Clocking 
        state_dict = {
            'state_list':'',
            'state_wo_list':''
        }    
        state_dict = self._prepare_invisible_action_start_stop_wo(state_dict)
        for rec in self:            
            rec.is_invisible_action_invoice_create = rec.state != rec._prepare_invisible_action_invoice_create_state(state)
            rec.is_invisible_action_start_stop_wo = (
                rec.state != state_dict['state_list']
            ) or (rec.state_wo == 'finish')            
            rec.is_invisible_action_open = True

    # 12: override methods

    def _prepare_rfa(self,obj_po):
        pass

    def get_rfa_additional_vals(self):
        vals = super().get_rfa_additional_vals()
        vals.update({
            'wfa_uid': self.env.uid,
            'wfa_date': datetime.now()
        })
        return vals
    
    def get_approve_additional_vals(self):
        vals = super().get_approve_additional_vals()
        if not self.confirm_date:
            self.action_confirm()
        vals.update({
            'approved_uid': self.env.uid,
            'approved_date': datetime.now()
        })
        return vals
    
    def action_request_approval(self):
        self._prepare_rfa(self)
        if not self.order_line:
            raise ValidationError("Produk belum diisi")
        for line in self.order_line:
            line.get_quantity_available(line.order_id.company_id.id, line.product_id.id, line.division, line.order_id._get_location_wo(line.order_id.company_id.id)['source']) 
        
        rfa = super().action_request_approval()
        return rfa

    def action_confirm(self):
        self._validate_order()
        self._prepare_confirmation()
        return super(TwWorkOrder,self.with_context(model_name='tw.work.order')).action_confirm()

    # NRFS Work Order
    def action_confirm_order(self):
        self._validate_order()
        if not self.order_line:
            raise ValidationError(('Error!'), _('You cannot confirm a work order without any work order line.'))
        self.write({
            'confirm_uid': self.env.uid, 
            'confirm_date': datetime.now(),
            'state': 'confirmed'
        })
        return True
    
    def validate_order(self):
        self._validate_order()
        return super().validate_order()
    
    def get_amount_discount(self):
        discount_parameter = self._get_discount_parameter()
        max_discount = 0.0  # Initialize with 0 or float('-inf') if negative discounts are possible
        
        for line in self.order_line:
            if line.division == 'Sparepart':
                if line.product_id.categ_id.name in ('OIL', 'GMO'):
                    if not discount_parameter.get('oil_discount'):
                        raise ValidationError("Oil Discount Parameter is not set")
                    curr_discount = line.discount * discount_parameter.get('oil_discount')
                else:
                    if not discount_parameter.get('sparepart_discount'):
                        raise ValidationError("Sparepart Discount Parameter is not set")
                    curr_discount = line.discount * discount_parameter.get('sparepart_discount')
            else:
                if not discount_parameter.get('other_discount'):
                    raise ValidationError("Other Discount Parameter is not set")
                curr_discount = line.discount * discount_parameter.get('other_discount')
                
            # Update max_discount if current discount is higher
            if curr_discount > max_discount:
                max_discount = curr_discount
        
        return max_discount

    # Clocking
    def _prepare_invisible_action_start_stop_wo(self,state_dict):
        if 'approved' not in state_dict['state_list']:
            state_dict['state_list'] = 'approved'

        prepare = super()._prepare_invisible_action_start_stop_wo(state_dict)
        return prepare
    
    def _prepare_invisible_action_invoice_create_state(self,state):
        if self.state == 'finished':
            state = 'finished'
        return state
    
    def _get_amount_field(self):
        return "approval_discount"
            
    def _get_discount_parameter(self):
        oil_discount_parameter = self.env['ir.config_parameter'].suspend_security().get_param('oil_discount_parameter')
        sparepart_discount_parameter = self.env['ir.config_parameter'].suspend_security().get_param('sparepart_discount_parameter')
        other_discount_parameter = self.env['ir.config_parameter'].suspend_security().get_param('other_discount_parameter')
        return {'oil_discount': int(oil_discount_parameter), 'sparepart_discount': int(sparepart_discount_parameter), 'other_discount': int(other_discount_parameter)}