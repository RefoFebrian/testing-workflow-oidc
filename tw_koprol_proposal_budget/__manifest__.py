# -*- coding: utf-8 -*-
{
    'name': "TW Koprol Budget",

    'summary': "TW Koprol Budget",

    'description': """
TW Koprol Budget
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
    'depends': [
            'base',
            'tw_base',
            'tw_koprol',
            'tw_payment_request',
            ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tw_budget_proposal_view.xml',
        'views/tw_payment_request_view.xml',
        'views/tw_menu.xml',

    ]
}

