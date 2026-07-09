# -*- coding: utf-8 -*-
{
    'name': "TW Report Branch Grading",

    'summary': "Report Branch Grading",

    'description': """
Laporan Branch Grading - Excel Report
Menampilkan detail grading cabang dan summary berdasarkan risk calculator.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'account',
        'tw_menu',
        'tw_base',
        'tw_branch',
        'tw_calculator_risk',
        'web_report',
    ],

    'data': [
        # Data files harus di load terlebih dahulu
        'data/parameters.xml',
        'data/filter.xml',

        'report/tw_report_branch_grading_view.xml',

        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
}
