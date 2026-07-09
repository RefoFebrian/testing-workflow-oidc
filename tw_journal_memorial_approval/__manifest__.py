# -*- coding: utf-8 -*-
{
    'name': "TW Journal Memorial Approval",

    'summary': "Adds an approval workflow to the TW Journal Memorial module for submitting and tracking journal memorial requests.",

    'description': """
Long description of module's purpose
    This module adds an approval workflow to the TW Journal Memorial module. It allows users to submit journal memorial requests for approval and track the status of these requests. The approval process can be customized to fit the organization's requirements, ensuring that all payments are properly reviewed and authorized before being processed.
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
        'tw_journal_memorial',
        'tw_approval',
        'tw_branch_setting',
    ],

    # always loaded
    'data': [
        'security/res_button_groups.xml',
        'security/res_groups.xml',
        'views/tw_journal_memorial_approval_view.xml',
        'views/tw_branch_setting_view.xml',
    ]
}

