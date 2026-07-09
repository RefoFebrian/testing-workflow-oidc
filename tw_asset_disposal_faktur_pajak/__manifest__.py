# -*- coding: utf-8 -*-
{
    'name': "TW Asset Disposal Faktur Pajak",

    'summary': "TW Asset Disposal Faktur Pajak Integration",

    'description': """
    TW Asset Disposal Faktur Pajak Integration
    - Adds Faktur Pajak mixin to Asset Disposal
    - Adds Faktur Pajak tab in Asset Disposal form
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    'depends': [
        'base',
        'tw_asset_disposal',
        'tw_faktur_pajak',
    ],

    'data': [
        'views/tw_asset_disposal_faktur_pajak_view.xml',
    ]
}
