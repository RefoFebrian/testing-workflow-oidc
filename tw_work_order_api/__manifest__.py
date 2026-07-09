# -*- coding: utf-8 -*-
{
    'name': "TW Work Order Api",

    'summary': "TW Work Order Api",

    'description': """
        TW Work Order Api
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_branch_setting',
        'tw_work_order',
        'stock',
        'tw_api',
        'rest_api',
        'web'
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',

        'views/tw_api_master_bundling_view.xml',
        'views/tw_work_order_inherit_view.xml',
        'views/tw_menu.xml',

        'data/tw_api_work_order_data.xml',
    ],
}

