# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"

    is_not_handover = fields.Boolean(string='Not Handover', default=False)
    notif_msg = fields.Char(string='Notification Message')

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        self.notif_msg = False
        self.is_not_handover = False
        messages = []
        lot = self.env['stock.lot'].sudo().search([('id', '=', self.lot_id.id)])
        if lot.vehicle_registration_receipt_id and not lot.registration_handover_id:
            messages.append("STNK")
        
        if lot.vehicle_ownership_receipt_id and not lot.ownership_handover_id:
            messages.append("BPKB")
        if messages:
            self.notif_msg = "Dokumen %s belum dilakukan penyerahan." % " dan ".join(messages)
            self.is_not_handover = True