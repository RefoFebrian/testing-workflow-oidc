# -*- coding: utf-8 -*-
{
    'name': "TW Approval",

    'summary': "multi-level approval workflows based on predefined rules, user roles, and conditions.",

    'description': """
        The Approval Matrix module is designed to manage structured 
        and flexible approval processes within the Odoo system. 
        This module enables organizations to define and enforce 
        multi-level approval workflows based on predefined rules, user roles, and conditions.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','tw_base','tw_selection','tw_hr','rest_api'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'views/tw_menu_view.xml',
        'views/tw_approval_config_view.xml',
        'views/tw_approval_copy_view.xml',
        'views/tw_approval_matrix_view.xml',
        'views/tw_approval_portal_view.xml',
        'views/tw_approval_view.xml',
    ],
}

