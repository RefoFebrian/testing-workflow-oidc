# -*- coding: utf-8 -*-
{
    'name': "TW Stock Opname Direct Gift",
    'version': '1.0.0',
    'summary': "Stock Opname Direct Gift",

    'description': """
Long description of module's purpose
    """,

    'author': "Tunas Honda",
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',

    'category': 'Uncategorized',

    'depends': ['base', 'tw_stock', 'tw_attachment', 'web_report', 'tw_pilot_project'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'report/tw_stock_opname_dg_report.xml',
        'report/tw_dg_print_validasi_view.xml',
        'report/tw_stock_opname_direct_gift_print_bakso_view.xml',

        'views/tw_stock_opname_direct_gift_view.xml',
        'views/tw_menu.xml',

        'wizards/tw_stock_opname_bakso_dg_view.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
