# -*- coding: utf-8 -*-
{
    'name': "TW Business Trip Approval",

    'summary': "TW Business Trip Approval",

    'description': """
TW Business Trip Approval
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
    'depends': ['base','tw_business_trip','tw_approval'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_business_trip_view.xml',

    ],
}

