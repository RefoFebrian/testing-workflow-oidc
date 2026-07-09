# -*- coding: utf-8 -*-
{
    'name': "TW Payment Request Proposal",

    'summary': "Connect Payment Request and Proposal.",

    'description': """
This module connect Payment Request and Proposal.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_payment','tw_payment_request','tw_proposal','tw_payment_proposal'],

    # always loaded
    'data': [
        'views/tw_payment_request_view.xml',
    ]
}

