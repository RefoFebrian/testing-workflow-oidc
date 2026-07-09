# -*- coding: utf-8 -*-
{
    'name': "TW LBB Report",

    'summary': "TW LBB Report",

    'description': """
        TW LBB Report
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'tw_menu',
        'web_report'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'views/tw_lbb_report_view.xml',
        'views/tw_menu.xml',
    ],
}

