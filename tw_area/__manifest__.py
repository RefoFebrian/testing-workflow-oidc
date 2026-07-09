# -*- coding: utf-8 -*-
{
    'name': "TW Area",

    'summary': "Area of Branches",

    'description': """
        Module Area of TDM   
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",
    "images": ["static/description/images/main_screenshot.jpg"],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_menu','tw_branch'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
                
        'views/tw_res_area_view.xml',
        'views/tw_res_users_inherit_view.xml',
        'views/tw_menu_view.xml',

        # 'data/res_area.xml', #? : Hidupkan sesuai kebutuhan saja, untuk prod tidak perlu 
    ],
}

