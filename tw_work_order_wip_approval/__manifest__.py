# -*- coding: utf-8 -*-
{
    'name': "TW Work Order WIP Approval",

    'summary': "TW Work Order WIP Approval",

    'description': """
TW Work Order WIP Approval
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
    'depends': ['base','tw_approval','tw_work_order_wip'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_work_order_wip_views.xml',
    ],
   
}

