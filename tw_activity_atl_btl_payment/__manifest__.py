# -*- coding: utf-8 -*-
{
    'name': "TW Activity Plan ATL BTL Payment",

    'summary': "Connector module for ATL/BTL activity and TW Payment modules.",

    'description': """
This module acts as a connector between the ATL/BTL Activity module and the TW Advance Payment module in Odoo.
It enables seamless integration and data flow for creation of advance payment related to ATL & BTL activities.
Use this module to ensure that approved ATL/BTL activities are properly linked with advance payment workflows.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': [
        'base', 
        'tw_base', 
        'tw_menu',
        'tw_account_setting',
        'tw_activity_atl_btl',
        'tw_advance_payment',
        'tw_payment_request',
        'tw_settlement',
        'tw_attachment',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'data/tw_selection_expense_source.xml',
        'data/tw_master_expense_source_data.xml',
        'data/tw_attachment_allowed_extension.xml',

        'views/tw_account_settings_inherit_view.xml',
        'views/tw_activity_atl_btl_inherit_view.xml',
        'views/tw_activity_atl_btl_line_inherit_view.xml',
        'views/tw_activity_atl_btl_settlement_view.xml',
        'views/tw_master_expense_source_view.xml',

        'wizard/tw_activity_settlement_wizard_view.xml',
        
        'views/tw_menu.xml',

    ]
}

