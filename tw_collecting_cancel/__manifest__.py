# -*- coding: utf-8 -*-
{
    'name': "TW Collecting Cancellation",

    'summary': "Add a cancellation workflow to the TW Collecting module for submitting and tracking requests.",

    'description': """
Long description of module's purpose
    This module adds a cancellation workflow to the TW Collecting module. It allows users to submit requests for cancellation.
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
    'depends': [
        'base',
        'tw_base',
        'tw_collecting',
        'tw_approval'
    ],

    # always loaded
    'data': [
        'security/res_button_groups.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        'views/tw_collecting_cancel_view.xml',
        'views/tw_menu.xml',
    ]
}

