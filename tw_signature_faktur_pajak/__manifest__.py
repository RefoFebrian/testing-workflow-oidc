# -*- coding: utf-8 -*-
{
    'name': "TW Signature Faktur Pajak",

    'summary': "Signature untuk Faktur Pajak",

    'description': """
        Module penghubung antara TW Signature dengan TW Faktur Pajak.
        Menambahkan field signature_id pada tw.faktur.pajak.out.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['tw_signature', 'tw_faktur_pajak'],

    'data': [
        'views/tw_faktur_pajak_out_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
