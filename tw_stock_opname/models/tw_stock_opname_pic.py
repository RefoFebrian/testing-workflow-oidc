from odoo import models, fields
from datetime import datetime

class StockOpnamePicWizard(models.TransientModel):
    _name = "tw.stock.opname.pic"
    _description = "Wizard Stock Opname PIC"

    def _get_default_datetime(self):
        return datetime.now()
    
    opname_id = fields.Many2one('tw.stock.opname', ondelete="cascade") 
    so_unit_pic_ids = fields.One2many('tw.stock.opname.pic.line','so_pic_id', domain=[('line_type', '=', 'unit')], context={'default_line_type': 'unit'})
    so_accessories_pic_ids = fields.One2many('tw.stock.opname.pic.line','so_pic_id', domain=[('line_type', '=', 'accessory')], context={'default_line_type': 'accessory'})

    def action_generate_pic(self):
        detail_so_units = []
        for line in self.so_unit_pic_ids:
            detail_opname = self.env['tw.stock.opname.upload'].sudo().get_detail(line.location_id.id, self.opname_id.id)
            detail_id = tuple(detail_opname[0]['id'])

            detail_so_units.append([1, detail_id, {
                'employee_id': line.employee_id.id,
                'has_accessories': line.has_accessories,
                'is_showroom': line.is_showroom,
            }])
        
        detail_so_accessories = []
        for line in self.so_accessories_pic_ids:
            detail_accessories_opname = self.env['tw.stock.opname.upload'].sudo().get_detail_accessories(line.location_id.id, self.opname_id.id)
            detail_id = tuple(detail_accessories_opname[0]['id'])

            detail_so_accessories.append([1, detail_id, {
                'employee_id': line.employee_id.id,
            }])

        self.opname_id.write({
            'detail_opname_ids' : detail_so_units,
            'detail_accessories_ids': detail_so_accessories,
            'state':'in_progress',
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_datetime()
        })