# -*- coding: utf-8 -*-
{
    'name': "Website Self Register",

    'summary': "Website for Self Register (HONDA)",

    'description': """
Website for Self Register (HONDA)
    """,
    'license': 'LGPL-3',

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website/Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/self_register_non_active_view.xml',
        'views/self_register_assets_js.xml',
        'views/self_register_thank_you_view.xml',
        # 'views/self_register_home_view.xml',
        'views/self_register_new_home.xml',
    ],
}

