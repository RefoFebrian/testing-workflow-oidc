# -*- coding: utf-8 -*-
{
    'name': "TW Advance Payment Proposal",

    'summary': "TW Advance Payment Proposal",

    'description': """
TW Advance Payment Proposal
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
    'depends': ['base','tw_base','tw_advance_payment','tw_payment','tw_payment_proposal'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_advance_payment_proposal_view.xml',
    ]
}

