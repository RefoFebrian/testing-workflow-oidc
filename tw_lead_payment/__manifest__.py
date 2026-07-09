# -*- coding: utf-8 -*-
{
    'name': "TW Lead with Payment",

    'summary': "Lead with data of Payment like down payment",

    'description': """
    Lead with data of Payment like down payment
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_lead'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
}

