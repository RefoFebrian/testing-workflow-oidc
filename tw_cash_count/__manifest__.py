# -*- coding: utf-8 -*-
{
    'name': "TW Cash Count",

    'summary': "TW Cash Count",

    'description': """
TW Cash Count
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
    'depends': ['base','tw_base','tw_bank_transfer','tw_petty_cash'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_group_buttons.xml',
        'security/ir_rule.xml',

        'views/tw_cash_count_view.xml',
        'views/tw_cash_count_validation.xml',
        'views/res_branch_setting_view.xml',

        'reports/tw_berita_acara_cash_count_report_view.xml',

        'views/tw_menu.xml',

    ]
}

