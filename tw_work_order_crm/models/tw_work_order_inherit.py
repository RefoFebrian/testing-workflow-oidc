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
    member = fields.Char(string='Member')
    is_own_dealer = fields.Selection([
        ('ya', 'Dealer Sendiri'),
        ('tidak', 'Dealer Lain')
    ], default="tidak", string='Asal Pembelian')
    relationship_with_the_owner_id = fields.Many2one('tw.selection', string='Hubungan Dengan Pemilik', domain=[('type', '=', 'HubunganDenganPemilik')])

    # Selection
    consumer_age = fields.Selection([
        ('<25', '<25'),
        ('26-35', '26-35'),
        ('36-50', '36-50'),
        ('>50', '>50')
    ], string='Usia Konsumen')

    # 9: relation fields
    gender_id =  fields.Many2one('tw.selection', string='Jenis Kelamin' , domain=[('type','=','Gender')])
    job_id = fields.Many2one('tw.selection', string='Pekerjaan Konsumen', domain="[('type', '=', 'Occupation')]")

    # 10: constraints & sql constraints
    @api.constrains('relationship_with_the_owner_id')
    def _constrain_relationship_owner(self):
        if self.relationship_with_the_owner_id.value == 'sendiri':
            # Check if customer_stnk_id differs from partner_id
            if self.customer_stnk_id and self.partner_id:
                if self.customer_stnk_id != self.partner_id:
                    raise ValidationError('Hubungan dengan pemilik adalah "Sendiri", namun data Customer STNK berbeda dengan Partner.\nMohon periksa kembali data yang diinputkan.')

    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        onchange = super(TwWorkOrder, self)._onchange_company_id()
        self.relationship_with_the_owner_id = False
        return onchange

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        onchange = super(TwWorkOrder, self)._onchange_partner_id()
        if self.partner_id:
            self.gender_id = self.partner_id.gender_id.id
            self.consumer_age = self.partner_id.consumer_age
            self.job_id = self.partner_id.occupation_id.id
        else:
            self.gender_id = False
            self.consumer_age = False
            self.job_id = False
        self._prepare_customer_stnk_id()
        return onchange

    @api.onchange('type_id','company_id')
    def onchange_type_new(self):
        self.customer_type = False
        onchange = super(TwWorkOrder, self).onchange_type_new()
        return onchange

    # 12: override methods

    def _prepare_vals_before_create(self,vals):
        vals = super(TwWorkOrder, self)._prepare_vals_before_create(vals)
        if vals.get('mobile'):
            normalize_mobile = self._normalize_with_lib(vals['mobile'])
            if len(normalize_mobile) < 6:
                raise ValidationError("Mobile tidak boleh kurang dari 6 digit!")
            elif not normalize_mobile.isdigit():
                raise ValidationError(_("Nomor Handphone harus berupa angka!"))
            vals.update({'mobile': normalize_mobile})
        return vals
    
    def _update_partner(self, vals):
        if not vals['customer_stnk_id']:
            return
        partner = self.env['res.partner'].browse(vals['customer_stnk_id'])
        if not partner:
            raise ValidationError(_('Partner not found!'))
        
        # Update the partner with the provided values
        partner.with_context(origin=self.name).sudo().write(
            {
                'mobile': vals['mobile'],
                # 'customer': True # field tidak ada
            }
        )

    def _prepare_previous_work_order(self):
        prepare_previous_work_order = super()._prepare_previous_work_order()
        # Work Order CRM
        self.reason_to_ahass_id = self.previous_work_order_id.reason_to_ahass_id.id
        self.mobile = self.previous_work_order_id.mobile
        self.relationship_with_the_owner_id = self.previous_work_order_id.relationship_with_the_owner_id.id
        self.gender_id = self.previous_work_order_id.gender_id.id
        self.consumer_age = self.previous_work_order_id.consumer_age
        self.job_id = self.previous_work_order_id.job_id.id
        self.member = self.previous_work_order_id.member
        self.is_own_dealer = self.previous_work_order_id.is_own_dealer if self.previous_work_order_id.is_own_dealer else 'tidak'
        return prepare_previous_work_order