# -*- coding: utf-8 -*-
{
    'name': "TW Report All Petty Cash",

    'summary': "TW Report All Petty Cash",

    'description': """
Report All Petty Cash
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
    'depends': ['base', 'web_report', 'tw_menu', 'tw_petty_cash', 'tw_bank_transfer', 'tw_branch', 'account'],

    # always loaded
    'data': [
        'report/tw_report_all_pettycash_view.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_menu.xml',
    ],
}