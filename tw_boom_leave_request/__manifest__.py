# -*- coding: utf-8 -*-

{
    'name': "TW BOOM Leave Request",

    'summary': "BOOM Leave Request module",

    'description': """
        This module provides tools to manage and monitoring 
        leave request for every employee. 
        It enables users to request leave and make his task on BOOM auto deleted when leave request is approved, 
        and make his task on BOOM auto restored when leave request is rejected.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'AGPL-3',

    'depends': ['base', 'hr', 'tw_base', 'tw_boom'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/scheduled_action.xml',

        'views/tw_boom_leave_request_view.xml',

        'views/tw_menu.xml',
    ],
    "installable": True,
	"auto_install": False,
	"application": True,
}
