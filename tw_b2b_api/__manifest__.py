# -*- coding: utf-8 -*-
{
    'name': "TW B2B API",

    'summary': "TW B2B API",

    'description': """
        TW B2B API
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
        'base_suspend_security',
        'tw_base',
        'tw_api',
        'rest_api'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}

