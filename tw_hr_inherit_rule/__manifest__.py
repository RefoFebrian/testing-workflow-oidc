# -*- coding: utf-8 -*-
{
    'name': "TW HR Inherit Rule",

    'summary': "HR Inherit Rule",

    'description': """
        HR Inherit Rule
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
    'depends': ['base','account'],

    # always loaded
    'data': [],
    'installable': True,
    'application': True,
    'post_init_hook': 'post_init_hook_function',
}

