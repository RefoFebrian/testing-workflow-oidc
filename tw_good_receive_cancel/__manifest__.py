# -*- coding: utf-8 -*-
{
    'name': "TW Good Receive Cancel",

    'summary': "Module for cancelling Good Receive transactions with approval workflow.",

    'description': """
TW Good Receive Cancel
======================

This module provides functionality to cancel Good Receive (GR) transactions in Odoo.
It ensures proper validations are in place before a GR can be canceled:
- Approval workflow integration
- Journal reversal for GR entries
- Stock return handling (for future use)
- Acquisition dependency check

The module integrates with tw_cancellation base module for consistent cancellation flow.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Inventory',
    'version': '18.0.0.1',
    'license': 'AGPL-3',

    'depends': [
        'base',
        'stock',
        'tw_base',
        'tw_cancellation',
        'tw_asset_management',
        'tw_account_setting',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_good_receive_cancel_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',
        
        'data/tw_cancellation_handler_data.xml',
    ],
}
