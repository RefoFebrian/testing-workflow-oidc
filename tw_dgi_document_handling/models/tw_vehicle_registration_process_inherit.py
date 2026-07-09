# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TWVehicleRegistrationProcess(models.Model):
    _name = "tw.vehicle.registration.process"
    _inherit = ["tw.vehicle.registration.process", "tw.dgi.info.mixin"]
    
    def action_open_dgi_wizard(self):
        """Open DGI wizard dari list view"""
        return {
            'name': 'Get Data from DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.proses.stnk.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.env.company.id,
            }
        }
