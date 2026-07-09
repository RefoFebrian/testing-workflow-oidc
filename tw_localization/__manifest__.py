# -*- coding: utf-8 -*-
{
    'name': "TW Master Localization",

    'summary': "Master Localization (City, District, Sub-District)",

    'description': """
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_menu'],

    # always loaded
    'data': [
        # ? Data is disabled, beacuse we want to import the complete localization with Excel file.
        # 'data/tw_res_country.xml',
        # 'data/tw_res_city.xml',
        # 'data/tw_res_district.xml',
        # 'data/tw_res_sub_district.xml',

        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/res_country_view.xml',
        'views/res_country_state_view.xml',
        'views/res_city_view.xml',
        'views/res_district_view.xml',
        'views/res_sub_district_view.xml',
        
        'views/tw_localization_menus.xml',
    ],
}

