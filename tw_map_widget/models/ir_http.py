# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        
        provider_model = self.env['base.geocoder']._get_provider()
        provider = provider_model.tech_name if provider_model else 'openstreetmap'
        api_key = self.env['ir.config_parameter'].sudo().get_param('base_geolocalize.google_map_api_key') or ''

        result['tw_map_widget'] = {
            'provider': provider,
            'google_map_api_key': api_key,
        }
        return result
