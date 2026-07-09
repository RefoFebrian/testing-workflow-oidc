# -*- coding: utf-8 -*-
{
    'name': "TW Mutation Request Approval",

    'summary': "Approval for Module Mutation Request",

    'description': """
        Approval for Module Mutation Request
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_mutation_request','tw_approval'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_mutation_request_approval_view.xml',
    ],
    'application':True,
    'installable':True,
}

