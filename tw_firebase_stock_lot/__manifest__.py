# -*- coding: utf-8 -*-
{
    'name': "TW Firebase Stock Lot",

    'summary': "Modular for stock lot and firebase notification",

    'description': """
TW Firebase Stock Lot
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_firebase', 'tw_stock'],

    # always loaded
    'data': [
        "views/tw_firebase_notification_inherit_view.xml",
    ],

}

