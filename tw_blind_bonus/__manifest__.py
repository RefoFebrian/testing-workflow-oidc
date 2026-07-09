# -*- coding: utf-8 -*-
{
    'name': "TW Blind Bonus",

    'summary': "Blind Bonus Management for Tunas Group",

    'description': """
        This module handles blind bonus functionality including:
        - Blind bonus amount configuration per branch
        - Journal configuration for blind bonus transactions
        - Automatic blind bonus invoice creation on sales
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_sale',
        'tw_branch_setting',
        'tw_account_setting',
        'tw_purchase_order',
        'tw_account_purchase',
        'tw_purchase_order_cancel',
        'tw_sale_order_cancel'
    ],

    # always loaded
    'data': [
        'views/tw_branch_setting_view.xml',
        'views/tw_account_setting_view.xml'
    ],
    'installable': True,
    'application': True,
}
