# -*- coding: utf-8 -*-
{
    'name': "TW Account Report Filter",

    'summary': "TW Account Report Filter",

    'description': """
TW Account Report Filter
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",
    'category': 'Accounting/Payment',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','tw_base','tw_menu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_account_report_filter_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

