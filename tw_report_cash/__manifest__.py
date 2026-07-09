# -*- coding: utf-8 -*-
{
    'name': "TW Report Cash",

    'summary': "TW Report Cash",

    'description': """
Report Cash
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'web_report',
        'tw_base',
        'tw_menu',
        'tw_branch',
        'tw_partner',
        'tw_account',
        'tw_petty_cash',
        'tw_bank_transfer',
        'tw_register_kwitansi',
        'tw_payment',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_report_cash_report.xml',
        'report/tw_report_cash_templates.xml',
        'views/tw_report_cash_view.xml',
        'views/tw_menu.xml',
    ],
}