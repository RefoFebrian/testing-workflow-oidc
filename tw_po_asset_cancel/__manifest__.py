# -*- coding: utf-8 -*-
{
    'name': "TW Purchase Order Asset Cancel",

    'summary': "Manage cancellation of Purchase Order Asset.",

    'description': """
        This module provides functionality to cancel Purchase Order Asset with approval workflow.
        Key features include:
        - Cancel Purchase Order Asset with approval process
        - Validation to ensure no active Good Receive before cancellation
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

        'views/tw_purchase_order_asset_cancel_view.xml',

        'views/tw_menu.xml',
    ],
}