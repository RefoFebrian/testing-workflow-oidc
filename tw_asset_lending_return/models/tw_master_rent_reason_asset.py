from odoo import models, fields, api, _

class TwMasterRentReasonAsset(models.Model):
    _name = "tw.master.rent.reason.asset"
    _order = "name ASC"
    _description = "Master Reason Peminjaman Asset"

    name = fields.Char(string="Alasan Peminjaman Asset")

    _sql_constraints = [('name_unique', 'unique(name)', 'Master alasan peminjaman asset tidak boleh duplikat.')]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list: 
            if vals.get('name'):
                vals['name'] = str(vals['name']).strip().upper()
        return super(TwMasterRentReasonAsset, self).create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).strip().upper()
        return super(TwMasterRentReasonAsset, self).write(vals)
