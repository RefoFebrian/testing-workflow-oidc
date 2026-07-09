# -*- coding: utf-8 -*-
{
    'name': "TW Signature",

    'summary': "Master Signature",

    'description': """
        Master data untuk Signature pada report dan dokumen.
        Digunakan untuk menentukan siapa yang menandatangani dokumen.
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
        
        'views/tw_signature_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
}
