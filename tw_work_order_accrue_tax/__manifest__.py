# -*- coding: utf-8 -*-
{
    'name': "TW Work Order Accrue Tax",

    'summary': "TW Work Order Accrue Tax",

    'description': """
        TW Work Order Accrue Tax
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_work_order',
        'tw_work_order_claim',
        'tw_work_order_cancel',
        'tw_account_setting',
    ],

    # always loaded
    'data': [
        'data/schedulle_work_order_accrue_tax.xml',

        'views/tw_account_setting_inherit_view.xml',
        'views/tw_work_order_inherit_view.xml',
    ],
}
