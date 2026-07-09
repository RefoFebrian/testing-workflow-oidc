# -*- coding: utf-8 -*-
{
    'name': "TW Mutation Report",

    'summary': "TW Mutation Report",

    'description': """
        TW Mutation Report
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
        'tw_menu',
        'tw_base',
        'tw_branch',
        'tw_partner',
        'tw_account',
        'tw_product',
        'tw_mutation'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_mutation_detail_report_view.xml',

        'views/tw_menu.xml',
    ],
}

