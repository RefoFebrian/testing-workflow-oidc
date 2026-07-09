# -*- coding: utf-8 -*-
{
    'name': "TW Approval Delegation",

    'summary': "Temporary approval delegation for employees on leave.",

    'description': """
        Manage temporary approval delegation by assigning an employee's
        approval group to another employee for a limited period.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['mail', 'tw_approval', 'tw_hr'],

    'data': [
        # Security Data
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        #
        'data/ir_sequence_data.xml',
        'data/tw_approval_config_data.xml',
        'data/ir_cron_data.xml',

        # Views
        'views/tw_approval_delegation_view.xml',

        # Menu
        'views/tw_menu_view.xml',
    ],
}
