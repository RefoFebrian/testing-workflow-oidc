# -*- coding: utf-8 -*-
{
    'name': "TW Incentive Approval",

    'summary': "Module to manage and approve employee incentive requests",

    'description': """
This module provides functionality for submitting, tracking, and approving employee incentive requests. It streamlines the approval workflow, ensures transparency, and maintains records of all incentive approvals within the organization.
    """,

    'author': "TunasHonda",
    'website': "https://www.honda-ku.com",

    'category': 'TW HR / TW HR',
    'version': '0.1',
    "license": "LGPL-3",

    'depends': ['base', 'tw_hr', 'tw_incentive', 'tw_approval'],

    'data': [
        # 'data/approval_data.xml',
        'security/res_groups_button.xml',
        'views/tw_master_incentive_inherit_view.xml',
        'views/tw_master_target_margin_inherit_view.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}

