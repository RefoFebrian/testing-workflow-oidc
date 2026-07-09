# -*- coding: utf-8 -*-
{
    'name': "TW Advance Payment Approval",

    'summary': "TW Advance Payment Approval",

    'description': """
    TW Advance Payment Approval module, this module adds approval function
    to Advance Payment module.
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
    'depends': ['base','tw_base','tw_approval','tw_advance_payment'],

    # always loaded
    'data': [
        "security/res_groups_button.xml",
        "security/ir.model.access.csv",
        
        'views/tw_advance_payment_view.xml',

    ],
}

