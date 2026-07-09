# -*- coding: utf-8 -*-
{
    'name': "TW Remark Faktur Pajak",

    'summary': "Remark untuk Faktur Pajak",

    'description': """
        Module penghubung antara TW Remark dengan TW Faktur Pajak.
        Menambahkan helper method untuk mendapatkan remark berdasarkan model transaksi.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['tw_remark', 'tw_faktur_pajak'],

    'data': [
        'views/tw_faktur_pajak_out_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
