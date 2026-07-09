# -*- coding: utf-8 -*-
{
    'name': "TW Activity Plan ATL BTL Approval",

    'summary': "Module to manage and streamline activity ATL & BTL approvals.",

    'description': """
This module provides functionality to manage the approval process for activity ATL & BTL in Odoo. 
It allows users to define approval workflows, set approval limits, and track the status of activity ATL & BTL 
throughout the approval process. Key features include: Configurable approval levels and rules

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
    'depends': ['base', 'tw_base', 'tw_selection', 'tw_approval', 'tw_activity_atl_btl',],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'views/tw_activity_atl_btl_approval_view.xml',
        'views/tw_activity_atl_btl_line_approval_view.xml',
        'views/tw_activity_atl_btl_line_reject_view.xml',
        'views/tw_activity_atl_btl_line_revision_view.xml',
        'views/tw_menu_view.xml',
    ]
}

