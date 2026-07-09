# -*- coding: utf-8 -*-
{
    'name': "TW PUST (Penerimaan Uang Setoran Tunai)",

    'summary': """
        Manages PUST (Cash-in-Transit) process for Bank Transfer.
        Facilitates Cash → Transit → Bank deposit workflow.
    """,

    'description': """
        TW PUST Module
        ==============
        This module extends the Bank Transfer functionality to manage
        PUST (Penerimaan Uang Setoran Tunai) process:

        - Adds 'Transit' journal type to account.journal (MN01xxx).
        - Automates Cash-to-Transit and Transit-to-Bank workflows.
        - Links transit records with bidirectional references (pust_ref / transit_ref).
        - Integrates with Pilot Project for branch-level feature flagging.
        - Filters payment journals by PUST status (is_pusted).
        - Provides action_check_pust to verify cash journal balances.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'account',
        'tw_base',
        'tw_branch',
        'tw_bank_transfer',
        'tw_pilot_project',
        'tw_petty_cash',
        'tw_payment',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/tw_pust_bank_transfer_view.xml',
    ],
}
