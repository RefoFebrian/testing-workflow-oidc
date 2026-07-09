# -*- coding: utf-8 -*-
{
    'name': "TW Map Widget",
    'summary': """
        A Map Widget integrating with base_geolocalize (Google Maps & OpenStreetMap/Leaflet)
    """,
    'description': """
        This module provides an OWL field widget for Maps.
        It supports OpenStreetMap (via Leaflet.js) and Google Maps API based on settings in base_geolocalize.
    """,
    'author': "Liong",
    'category': 'Tools/UI',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'base_geolocalize'],
    'data': [
        # views, security, etc.
    ],
    'assets': {
        'web.assets_backend': [
            'tw_map_widget/static/src/css/leaflet.css',
            'tw_map_widget/static/src/css/map_widget.css',
            'tw_map_widget/static/src/js/leaflet.js',
            'tw_map_widget/static/src/js/map_widget.js',
            'tw_map_widget/static/src/xml/map_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
