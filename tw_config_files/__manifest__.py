# -*- coding: utf-8 -*-
{
    'name': "TW Config Files",

    'summary': "Configuration for saving Files into desired directory",

    'description': """
    Configuration Files
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_menu','tw_selection'],

    # always loaded
    'data': [
        'data/selection_data.xml',
        'data/image_extensions.xml',
        
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_config_files_view.xml',
        'views/tw_stored_files_view.xml',
    ],
}

