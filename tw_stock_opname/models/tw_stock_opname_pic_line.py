from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime

class StockOpnamePicLineWizard(models.TransientModel):
    _name = "tw.stock.opname.pic.line"
    _description = "Wizard Stock Opname PIC Line"

    def _get_default_datetime(self):
        return datetime.now()

    has_accessories = fields.Boolean(string='Has Accessories')
    is_showroom = fields.Boolean(string='Is Showroom')
    line_type = fields.Selection([('unit', 'Unit'), ('accessory', 'Accessory')], string='Type', required=True)
    
    so_pic_id = fields.Many2one('tw.stock.opname.pic', ondelete="cascade")
    # TODO : Pastikan Domain User
    employee_id = fields.Many2one('hr.employee', string='Penanggung Jawab')
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", related='employee_id.company_id')
    location_id = fields.Many2one('stock.location', string="Location")

    @api.model_create_multi
    def create(self, vals_list):
        for data in vals_list:
            if not data.get('employee_id'):
                raise Warning("PIC Belum Terisi, Cek Kembali.")
        return super(StockOpnamePicLineWizard, self).create(vals_list)