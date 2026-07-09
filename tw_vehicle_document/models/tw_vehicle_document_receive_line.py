# tw_document_handling/models/tw_vehicle_document_receive_line.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TwVehicleDocumentReceiveLine(models.Model):
    _name = "tw.vehicle.document.receive.line"
    _description = "Penerimaan Faktur Line"
    _inherit = ['vehicle.document.line.mixin']
    _order = "id desc"
    
    print_date = fields.Date(string='Tanggal Cetak')
    doc_number = fields.Char(string='No Faktur STNK')
    
    vehicle_document_receive_id = fields.Many2one(
        'tw.vehicle.document.receive', 
        string="Vehicle Document Receive", 
        ondelete='cascade'
    )

    @api.constrains('lot_id')
    def _check_duplicate_lot(self):
        for line in self:
            if line.lot_id and line.vehicle_document_receive_id:
                existing_lines = self.search([
                    ('id', '!=', line.id),
                    ('lot_id', '=', line.lot_id.id),
                    ('vehicle_document_receive_id', '=', line.vehicle_document_receive_id.id)
                ])
                if existing_lines:
                    raise ValidationError(_(
                        'Nomor mesin %s sudah ada di dokumen ini. '
                        'Silakan pilih nomor mesin yang lain.') % line.lot_id.name)
    
    def action_cancel(self):
        cancel = super().action_cancel()
        for rec in self:
            rec.lot_id.suspend_security().write({
                'vehicle_document_receive_id': False,
                'vehicle_document_receive_date': False,
                'print_date': False,
                'doc_number': False,
                'document_state': 'document_request',
            })
        return cancel