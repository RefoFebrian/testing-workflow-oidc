# -*- coding: utf-8 -*-
{
    'name': "TW Asset Disposal Hutang Lain",

    'summary': "Extension module for managing Hutang Lain data in tw_asset_disposal.",

    'description': """
        This module extends the functionality of tw_asset_disposal to streamline and enhance the management of Hutang Lain data.
    """,

    'author': "PT. Tunas Dwipa Matra",
    'website': "https://www.yourcompany.com",

    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    'depends': [
        'base',
        'tw_base',
        'tw_asset_disposal',
        'tw_asset_disposal_approval',
        'tw_payment',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'views/tw_asset_disposal_inherit_view.xml',
        'views/tw_account_setting_inherit_view.xml',
    ],
}
