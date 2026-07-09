# -*- coding: utf-8 -*-
{
    'name': "TW Selection",

    'summary': "Base Selection List",

    'description': """
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base', 'tw_menu'],

    # always loaded
    'data': [
        'data/tw_selection_data.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_selection_view.xml',

        'views/tw_menu.xml',
    ],

    'application':True,
    'installable':True,
}

