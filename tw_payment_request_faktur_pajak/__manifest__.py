# -*- coding: utf-8 -*-
{
    'name': "TW Payment Request Faktur Pajak",

    'summary': "TW Payment Request Faktur Pajak Integration",

    'description': """
    TW Payment Request Faktur Pajak Integration
    - Adds Faktur Pajak mixin to Payment Request
    - Adds Faktur Pajak tab in Payment Request form
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    'depends': [
        'base',
        'tw_payment_request',
        'tw_faktur_pajak',
    ],

    'data': [
        'views/tw_payment_request_faktur_pajak_view.xml',
    ]
}
