# -*- coding: utf-8 -*-
{
    'name': "TW Proposal",

    'summary': "Module of Proposal",

    'description': """
    This module is used by internal Main Dealer to manage proposal.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_base','tw_selection','tw_approval','tw_attachment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/res_groups_button.xml',

        'report/tw_proposal_report_template.xml',
        'views/tw_proposal_view.xml',

        'views/tw_menu.xml'
    ],
}

