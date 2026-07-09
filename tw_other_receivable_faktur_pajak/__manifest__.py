# -*- coding: utf-8 -*-
{
    'name': "TW Other Receivable Faktur Pajak",

    'summary': "TW Other Receivable Faktur Pajak Integration",

    'description': """
    TW Other Receivable Faktur Pajak Integration
    - Adds Faktur Pajak mixin to Other Receivable
    - Adds Faktur Pajak tab in Other Receivable form
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    'depends': [
        'base',
        'tw_other_receivable',
        'tw_faktur_pajak',
    ],

    'data': [
        'views/tw_other_receivable_faktur_pajak_view.xml',
    ]
}
