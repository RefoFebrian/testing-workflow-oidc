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


class TwReturnAsset(models.Model):
    _name = "tw.asset.return"
    _description = "Pengembalian Aset"
    _order = "date DESC"

    def _get_default_date(self):
        return date.today()

    # 8: Fields
    name = fields.Char(string='No Pengembalian',index=True)
    date = fields.Date(string='Tanggal',default=_get_default_date)
    state = fields.Selection([
        ('draft','Draft'),
        ('confirmed','Confirmed')
    ], string='Status', default='draft')

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')

    # 9: Relation Fields
    company_id = fields.Many2one('res.company', string='Branch')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    item_ids = fields.One2many('tw.asset.return.line', 'return_id', string='Detail')

    # 10: constraints & sql constraints
    @api.constrains('item_ids')
    def _check_item_ids(self):
        if len(self.item_ids) <= 0:
            raise ValidationError("Detail pengembalian wajib diisi!")
        err_msg_dict = {}
        for x in self.item_ids:
            if x.rent_id.suspend_security().company_id.id != self.company_id.id:
                err_msg = 'Tidak ada peminjaman %s di %s' % (x.rent_id.name, self.company_id.name)
                if not err_msg_dict.get('pma_invalid',False):
                    err_msg_dict.update({
                        'pma_invalid': [err_msg]
                    })
                else:
                    if err_msg not in err_msg_dict['pma_invalid']:
                        err_msg_dict['pma_invalid'].append(err_msg)
        if err_msg_dict:
            raise ValidationError('\n'.join(sum(err_msg_dict.values(),[])))

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('company_id',False):
                raise Warning("Branch tidak boleh kosong!")
            branch_obj = self.env['res.company'].browse(vals['company_id'])
            vals['name'] = self.env['ir.sequence'].get_sequence_code('TWRA', branch_obj.code)
        return super(TwReturnAsset, self).create(vals_list)

    def unlink(self):
        for x in self:  
            if x.state != 'draft':
                raise Warning('Pengembalian selain status Draft tidak bisa dihapus!')
        return super(TwReturnAsset, self).unlink()

    def copy(self, default=None, context=None):
        raise Warning("Pengembalian aset tidak bisa diduplikasi!")

    # 13: action methods
    def action_confirm(self):
        # Tanggal kembali
        return_date = self._get_default_date()
        # Update to detail peminjaman
        item_ids_update = {}
        # Update to aset
        asset_ids_list = []
        # Error
        msg = ""
        for x in self.item_ids:
            if not item_ids_update.get(x.rent_line_id.rent_id.id):
                item_ids_update.update({x.rent_line_id.rent_id.id: []})
            item_ids_update[x.rent_line_id.rent_id.id].append([1, x.rent_line_id.id, {
                'state': 'done',
                'return_date': return_date,
                'condition_return': x.condition_return,
                'note': x.note
            }])
            
            x.asset_id.suspend_security().write({'rent_id': False,'employee_user_id': x.rent_line_id.original_employee_user_id.id})

        peminjaman_name = False
        try:
            for key,vals in item_ids_update.items():
                peminjaman_obj = self.env['tw.asset.lending'].suspend_security().browse(key)
                peminjaman_obj.suspend_security().write({'item_ids': vals})
                item_ids_not_done = self.env['tw.asset.lending.line'].search([
                    ('rent_id','=',key),
                    ('state','!=','done')
                ], limit=1)
                if item_ids_not_done:
                    peminjaman_obj.suspend_security().write({'state': 'partially_returned'})
                else:
                    peminjaman_obj.suspend_security().write({'state': 'done'})
        except Exception as e:
            self._cr.rollback()
            raise Warning('Terjadi kesalahan saat update Peminjaman Aset %s: %s' % (peminjaman_name if peminjaman_name else '', e))
        try:
            # Update pengembalian aset
            self.write({
                'state': 'confirmed',
                'confirm_uid': self._uid,
                'confirm_date': datetime.now()
            })
        except Exception as e:
            self._cr.rollback()
            raise Warning('Terjadi kesalahan saat update Pengembalian Aset %s: %s' % (self.name, e))

    # 14: private methods

    

   

   

