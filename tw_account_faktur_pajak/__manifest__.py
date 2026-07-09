# -*- coding: utf-8 -*-
{
    'name': "TW Account Faktur Pajak",

    'summary': "TW Account Faktur Pajak Integration",

    'description': """
    TW Account Faktur Pajak Integration
    - Adds Faktur Pajak mixin to Account Move (Invoice)
    - Adds Faktur Pajak tab in Invoice form
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    'depends': [
        'base',
        'tw_account',
        'tw_faktur_pajak',
    ],

    'data': [
        'views/tw_account_move_faktur_pajak_view.xml',
    ]
}
