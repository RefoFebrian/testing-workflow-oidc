# -*- coding: utf-8 -*-
{
    'name': "TW Global Warning",

    'summary': "Global Warning Dialog. Keep raise Warning Dialog even if the user navigate to another page",

    'description': """
        Global Warning Dialog. Keep raise Warning Dialog even if the user navigate to another page",
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
    ],
    # always loaded
    'data': [
        "views/assets.xml"
    ],
    'assets': {
        'web.assets_backend': [
            "tw_global_warning/static/src/xml/global_rpc_error_listener.xml",
            "tw_global_warning/static/src/js/global_rpc_error_listener.js"
            ],
        'web.assets_backend_lazy': [
            'tw_global_warning/static/src/views/**',
        ],
    },

}

