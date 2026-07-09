# -*- coding: utf-8 -*-
{
    'name': "TW Report Cash Count",

    'summary': "TW Report Cash Count",

    'description': """
Laporan Cash Count - Excel Report
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': [
        'base',
        'tw_menu',
        'tw_cash_count',
        'web_report',
    ],

    'data': [
        'report/tw_report_cash_count_view.xml',

        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/tw_menu.xml',
    ],
}
