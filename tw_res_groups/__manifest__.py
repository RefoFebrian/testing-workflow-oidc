# -*- coding: utf-8 -*-
{
    'name': "TW Res Groups Upload",

    'summary': "Upload Res Groups",

    'description': """
Upload Res Groups
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_res_groups_view.xml',
        'views/tw_menu.xml'
    ],
}

