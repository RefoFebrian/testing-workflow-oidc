# -*- coding: utf-8 -*-
{
    'name': "TW Checklist Tool Approval",
    'version': '1.0.0',
    'summary': "Checklist Tool Approval",

    'description': """
Long description of module's purpose
    """,

    'author': "Tunas Honda",
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',

    'category': 'Uncategorized',

    'depends': ['base', 'tw_checklist_tool', 'tw_approval', 'base_suspend_security', 'mail'],

    'data': [
        'security/res_groups_button.xml',
        'views/tw_checklist_tool_approval_view.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}