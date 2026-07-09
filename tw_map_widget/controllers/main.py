# -*- coding: utf-8 -*-
import requests
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class MapWidgetController(http.Controller):
    @http.route('/tw_map_widget/geocode', type='json', auth='user')
    def geocode_address(self, address, **kw):
        if not address:
            return {}

        geocoder = request.env['base.geocoder']
        result = geocoder.geo_find(address)

        if result:
            return {
                'lat': result[0],
                'lng': result[1],
            }
        return {}

    @http.route('/tw_map_widget/reverse_geocode', type='json', auth='user')
    def reverse_geocode(self, lat, lng, **kw):
        if not lat or not lng:
            return {}

        provider = request.env['base.geocoder']._get_provider().tech_name
        
        if provider == 'googlemap':
            apikey = request.env['ir.config_parameter'].sudo().get_param('base_geolocalize.google_map_api_key')
            if apikey:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    'latlng': f"{lat},{lng}",
                    'key': apikey
                }
                try:
                    response = requests.get(url, params=params).json()
                    if response.get('status') == 'OK' and response.get('results'):
                        return {'address': response['results'][0]['formatted_address']}
                except Exception as e:
                    _logger.warning("Reverse geocoding failed: %s", e)
                return {} # If Google Map is chosen and has key but fails, don't fallback to OSM to avoid unexpected results.

        # Default to openstreetmap (if provider is openstreetmap, or googlemap without key)
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {'User-Agent': 'Odoo (http://www.odoo.com/contactus)'}
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lng
        }
        try:
            response = requests.get(url, headers=headers, params=params).json()
            if response and response.get('display_name'):
                return {'address': response['display_name']}
        except Exception as e:
            _logger.warning("Reverse geocoding failed: %s", e)

        return {}
