# -*- coding: utf-8 -*-
{
    'name': "TW Good Receive Asset Cancel",

    'summary': "Manage cancellation of Good Receive Asset.",

    'description': """
        This module provides functionality to cancel Good Receive Asset with approval workflow.
        Key features include:
        - Cancel Good Receive Asset with approval process
        - Validation to ensure no active Acquisition before cancellation
        - Validation to ensure invoice has not been paid before cancellation
        - Reverse journal JGR upon cancellation
        - Audit trail for cancellation process
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '18.0.0.1',
    'license': 'AGPL-3',

    'depends': [
        'base',
        'purchase',
        'tw_base',
        'tw_asset_management',
        'tw_cancellation',
        'tw_approval',
    ],

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/tw_good_receive_asset_cancel_view.xml',

        'views/tw_menu.xml',
    ],
}