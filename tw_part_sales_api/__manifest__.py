# -*- coding: utf-8 -*-
{
    'name': "TW Part Sales Api",

    'summary': "TW Part Sales Api",

    'description': """
        TW Part Sales Api
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
    'depends': ['base','tw_base','tw_part_sales','stock'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',

        'views/tw_part_sales_inherit_view.xml',

        'data/tw_part_sales_api_data.xml',
    ],
}

