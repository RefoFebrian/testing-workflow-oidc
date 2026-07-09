# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TWVehicleOwnershipHandover(models.Model):
    _name = "tw.vehicle.ownership.handover"
    _inherit = ["tw.vehicle.ownership.handover", "tw.dgi.info.mixin"] # Penyerahan BPKB
    
    # MD Reference
    md_reference_number = fields.Char(
        string='MD Reference Number',
        copy=False,
        readonly=True,
        index=True,
        help='Penyerahan BPKB (noENCB)',
    )
    
    def action_open_dgi_wizard(self):
        """Open DGI wizard dari list view"""
        return {
            'name': 'Get Data from DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.handover.bpkb.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.env.company.id,
            }
        }
