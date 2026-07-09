# -*- coding: utf-8 -*-
{
    'name': 'Trial Balance Report',
    'version': '18.0.0.0.1',
    'summary': 'Report Trial Balance',
    'description': """
        Module untuk generate laporan Trial Balance dalam format Excel.
        - Detail Trial Balance per Account
        - Import Sun Format
        - Import Trial Balance Format
    """,
    'author': 'Tunas Honda',
    'category': 'Accounting',
    'depends': [
        'base',
        'tw_base',
        'tw_account',
        'tw_branch',
        'tw_account_period',
        'tw_menu',
        'web_report',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/tw_trial_balance_report_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
