# -*- coding: utf-8 -*-
{
    'name': "TW Work Order KPB",

    'summary': "TW Work Order KPB",

    'description': """
TW Work Order KPB
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
    'depends': ['base','tw_work_order','tw_work_order_claim','tw_menu','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_work_order_inherit_view.xml',
        'views/tw_kpb_engine_type_view.xml',
        'views/tw_kpb_expired_view.xml',
        'views/tw_menu.xml',

        'data/tw_selection_data.xml',
    ],
}

