from datetime import datetime, date
from dateutil.relativedelta import relativedelta
# odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class SparepartSubstitusi(models.Model):
    _name = "tw.sparepart.substitusi"
    _description = "Sparepart Substitusi"
    _rec_name = "part_old_id"
    _order = "create_date desc"

    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    def _set_domain_part_id(self):
        domain = [('id','=',0)]
        products = self.env['product.product'].suspend_security()._get_product_ids_by_division('Sparepart')
        if products:
            domain = [('id','in',[x[0] for x in products])]
        return domain

    part_old_id = fields.Many2one('product.product', string='Sparepart Lama', domain=_set_domain_part_id)
    part_new_id = fields.Many2one('product.product', string='Sparepart Substitusi', domain=_set_domain_part_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft')
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')

    _sql_constraints = [('part_old_unique','UNIQUE(part_old_id)','Ditemukan data sparepart yang sama!')]

    @api.onchange('part_new_id')
    def _onchange_part_old_id(self):
        if self.part_old_id:
            if self.part_old_id == self.part_new_id:
                self.part_new_id = False
                raise Warning('Sparepart Substitusi tidak bisa sama dengan Sparepart Lama !')

    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise Warning('Perhatian!\nData berstatus selain Draft tidak bisa dihapus!')
        return super(SparepartSubstitusi, self).unlink()

    def action_confirm(self):
        self.write({
            'state': 'confirmed',
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_date()
        })