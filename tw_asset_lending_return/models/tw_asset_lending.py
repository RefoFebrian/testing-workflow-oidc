# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports
import logging

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)


class TwRentAsset(models.Model):
    _name = "tw.asset.lending"
    _inherit = ['tw.approval.mixin']
    _description = "Peminjaman Aset"
    _order = "date DESC"

    def _get_default_date(self):
        return date.today()

    # 8: Fields
    name = fields.Char(string='No Peminjaman',index=True)
    date = fields.Date(string='Tanggal',default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(name='Umum'), string='Divisi')
    
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')

    state = fields.Selection([
        ('draft','Draft'),
        ('open','Running'),
        ('partially_returned','Partially Returned'),
        ('done','Returned')
    ], string='Status', default='draft')
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')
    
    # 9: relation Fields
    company_id = fields.Many2one('res.company', string='Branch',default=lambda self: self.env.company)
    inter_company_id = fields.Many2one('res.company', string='Pinjam ke')
    employee_id = fields.Many2one('hr.employee',domain="[('company_id', '=', company_id)]", string='Penanggung Jawab')
    job_id = fields.Many2one('hr.job', string='Jabatan')
    item_ids = fields.One2many('tw.asset.lending.line', 'rent_id', string='Detail')   

    # 10: constraints & sql constraints
    @api.constrains('item_ids')
    def _check_item_ids_empty(self):
        if len(self.item_ids) <= 0:
            raise ValidationError("Detail peminjaman wajib diisi!")

    # 11: compute/depends & on change methods
    @api.onchange('employee_id')
    def _onchange_job_id(self):
        self.job_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id

    @api.onchange('start_date','end_date')
    def _onchange_start_end_date(self):
        if self.start_date and self.end_date:
            if self.start_date < self.date:
                raise ValidationError("Start date tidak boleh kurang dari tanggal peminjaman!")
            if self.start_date > self.end_date:
                raise ValidationError("Start date tidak boleh lebih dari end date!")

            if self.end_date < self.start_date:
                raise ValidationError("End date tidak boleh kurang dari start date!")
    
    # 12: override methods
    @api.model_create_multi 
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                company = self.env['res.company'].browse(vals['company_id'])
                vals['name'] = self.env['ir.sequence'].get_sequence_code('PMA', str(company.code))
        return super(TwRentAsset, self).create(vals_list)
  
    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise Warning('Peminjaman selain status Draft tidak bisa dihapus!')
        return super(TwRentAsset, self).unlink()

    def copy(self):
        raise Warning("Peminjaman aset tidak bisa diduplikasi!")

    # 13: action methods
    def action_confirm(self):
        # Tanggal pinjam
        rent_date = date.today()
        # Update to detail peminjaman
        item_ids_update = []
        # Error
        msg = ""
        for x in self.item_ids:
            sedang_dipinjam_id = self.env['tw.asset.lending.line'].search([
                ('asset_id','=',x.asset_id.id),
                ('state','=','open')
            ], limit=1)
            if sedang_dipinjam_id:
                msg += "Aset [%s] %s sedang dipinjam di %s. \n" % (x.asset_code, x.asset_id.name, sedang_dipinjam_id.rent_id.name)
            else:
                item_ids_update.append([1, x.id, {
                    'state': 'open',
                    'rent_date': rent_date,
                    'note': x.note,
                    'employee_id': x.asset_id.employee_user_id.id,  # Store current user
                    'original_employee_user_id': x.asset_id.employee_user_id.id,  # Store original user for restoration
                }])
            
            x.asset_id.write({'rent_id': self.id,'employee_user_id': x.employee_user_id.id})
        if msg:
            raise Warning(msg)
        try:
            self.write({
                'state': 'open',
                'confirm_uid': self._uid,
                'confirm_date': datetime.now(),
                'item_ids': item_ids_update
            })        
        except Exception as e:
            self._cr.rollback()
            raise Warning('Terjadi kesalahan saat update Peminjaman Aset %s: %s' % (self.name, e))

    # 14: private methods

    


