# -*- coding: utf-8 -*-
{
    'name': "TW Privacy Policy",

    'summary': "Privacy Policy check and acceptance for TETO system calling HOKI API",

    'description': """
        This module implements privacy policy check and acceptance flow for TETO system.
        It calls HOKI API to check if user has accepted the current privacy policy,
        and displays a modal for users who haven't accepted yet.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'tw_base', 'tw_api'],

    # always loaded
    'data': [
    ],

    'assets': {
        'web.assets_backend': [
            'tw_privacy_policy/static/src/js/privacy_policy.js',
        ],
    },

    'application': False,
    'installable': True,
}
