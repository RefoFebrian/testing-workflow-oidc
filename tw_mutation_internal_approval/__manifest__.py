# -*- coding: utf-8 -*-
{
    'name': "TW Mutation Internal Approval",

    'summary': "Mutation Internal connected to Approval",

    'description': """
        Mutation Internal connected to Approval
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
    'depends': ['base','base_suspend_security','tw_base','tw_mutation_internal','tw_approval','tw_stock'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_mutation_internal_approval_view.xml',
        'views/tw_stock_location_inherit_view.xml',
    ],
    'installable': True,
    'application': True,
}

