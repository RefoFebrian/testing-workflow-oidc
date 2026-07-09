# -*- coding: utf-8 -*-
{
    'name': "TW Expedition Apps",

    'summary': "Expedition Apps",

    'description': """
        Expedition Apps
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'base_suspend_security',
        'tw_stock',
        'tw_branch',
        'tw_hr',
        'tw_config_files',
        'rest_api',
        'tw_partner',
        'tw_mutation',
        'tw_sale',
        'tw_selection',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_stock_picking_inherit_view.xml',
        'views/tw_stock_move_line_inherit_view.xml',
        'views/tw_monitoring_expedition_apps_view.xml',
        'views/tw_partner_inherit_view.xml',
        'views/tw_assign_delivery_driver_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}

