# -*- coding: utf-8 -*-
{
    'name': "TW Remark",

    'summary': "Master Remark",

    'description': """
        Master data untuk Remark pada report dan dokumen.
        Digunakan untuk menentukan isi remark berdasarkan form/model transaksi.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base', 'tw_menu', 'tw_faktur_pajak'],

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_remark_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
}
