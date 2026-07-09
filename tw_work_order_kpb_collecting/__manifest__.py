# -*- coding: utf-8 -*-
{
    'name': "TW Work Order KPB Collecting",

    'summary': "TW Work Order KPB Collecting",

    'description': """
TW Work Order KPB Collecting
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
    'depends': ['base','tw_work_order_kpb','tw_work_order_collecting','tw_menu','tw_account_period','tw_account_setting'],

    # always loaded
    'data': [
        'views/tw_work_order_collecting_kpb_view.xml',
        'views/tw_menu.xml',
    ],
}

