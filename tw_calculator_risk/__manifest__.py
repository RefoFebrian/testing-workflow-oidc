# -*- coding: utf-8 -*-
{
    'name': "TW Calculator Risk",

    'summary': "Master Calculator Risk",

    'description': """
        Master data untuk Calculator Risk.
        Digunakan untuk menghitung risk score berdasarkan Financial, SLA, dan Percentage.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base', 'tw_menu', 'tw_base'],

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_calculator_risk_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
}
