# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class PartSales(models.Model):
    _name = "tw.part.sales"
    _inherit = ['tw.part.sales','tw.approval.mixin']

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('sent',),
        ('sale',),
        ('done',),
        ('cancel',),
        ('unused',),
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
    @api.depends('order_line.discount')
    def _compute_approval_discount(self):
        for rec in self:
            rec.approval_discount = rec.get_amount_discount()

    # 12: override methods

    def action_request_approval(self):
        if not self.order_line:
            raise ValidationError("Produk belum diisi")
        for line in self.order_line:
            line.get_quantity_available(line.order_id.company_id.id, line.product_id.id, line.product_id.categ_id.name, line.location_id.id)
        return super().action_request_approval()

    def get_rfa_additional_vals(self):
        vals = super().get_rfa_additional_vals()
        vals.update({
            'wfa_uid': self.env.uid,
            'wfa_date': datetime.now()
        })
        return vals

    def get_amount_discount(self):
        discount_parameter = self._get_discount_parameter()
        max_discount = 0.0  # Initialize with 0 or float('-inf') if negative discounts are possible
        
        for line in self.order_line:
            if line.product_id.categ_id.name in ('OIL', 'GMO'):
                if not discount_parameter.get('oil_discount'):
                    raise ValidationError("Oil Discount Parameter is not set")
                curr_discount = line.discount * discount_parameter.get('oil_discount')
            else:
                if not discount_parameter.get('sparepart_discount'):
                    raise ValidationError("Sparepart Discount Parameter is not set")
                curr_discount = line.discount * discount_parameter.get('sparepart_discount')
                
            # Update max_discount if current discount is higher
            if curr_discount > max_discount:
                max_discount = curr_discount
        
        return max_discount

    def _get_amount_field(self):
        return "approval_discount"

    def get_approve_additional_vals(self):
        vals = super().get_approve_additional_vals()
        vals.update({
            'approved_uid': self.env.uid,
            'approved_date': datetime.now()
        })
        return vals

    def _get_discount_parameter(self):
        oil_discount_parameter = self.env['ir.config_parameter'].suspend_security().get_param('oil_discount_parameter', '0')
        sparepart_discount_parameter = self.env['ir.config_parameter'].suspend_security().get_param('sparepart_discount_parameter', '0')
        other_discount_parameter = self.env['ir.config_parameter'].suspend_security().get_param('other_discount_parameter', '0')
        return {
            'oil_discount': int(oil_discount_parameter or 0),
            'sparepart_discount': int(sparepart_discount_parameter or 0),
            'other_discount': int(other_discount_parameter or 0),
        }