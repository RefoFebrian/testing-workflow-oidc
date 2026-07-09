# -*- coding: utf-8 -*-
{
    'name': "TW API Configuration and API Log",

    'summary': "API Configuration and API Log",

    'description': """
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'auth_oauth', 'tw_menu', 'tw_base', 'tw_selection'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_api_configuration_view.xml',
        'views/tw_endpoint_configuration_view.xml',
        'views/tw_api_log_view.xml',
        'views/tw_api_type_view.xml',
        'views/tw_menu.xml',

        'data/tw_api_configuration_type_data.xml',
        'data/tw_api_configuration_data.xml',
        'data/ir_config_parameter.xml',
    ],

    'application':True,
    'installable':True,
}
