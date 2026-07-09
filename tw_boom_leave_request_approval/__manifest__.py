# -*- coding: utf-8 -*-

{
    'name': "TW BOOM Leave Request Approval",

    'summary': "BOOM Leave Request Approval module",

    'description': """
        This module provides Approval flow for BOOM Leave Request module.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'AGPL-3',

    'depends': ['base', 'hr', 'tw_base', 'tw_approval', 'tw_boom_leave_request'],
    'data': [
        'data/tw_config_limit_approval_leave_request.xml',

        'security/res_groups_button.xml',

        'views/tw_boom_leave_request_approval_view.xml',
    ],
    "installable": True,
	"auto_install": False,
	"application": True,
}