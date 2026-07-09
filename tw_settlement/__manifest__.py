# -*- coding: utf-8 -*-
{
    'name': "TW Settlement",

    'summary': "This module is used to manage Settlement of Dealer and Employee.",

    'description': """
This module is used to manage Settlement of Dealer and Employee.
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
        'hr',
        'tw_base',
        'tw_web',
        'tw_menu',
        'tw_selection',
        'tw_advance_payment',
        'tw_account_setting',
        'tw_account_filter',
        'tw_attachment',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_group_button.xml',
        'security/ir_rule.xml',
        
        'report/tw_settlement_advance_payment_report_template.xml',
        
        'views/tw_settlement_view.xml',
        'views/tw_account_settings_view.xml',
        'views/tw_menu.xml',
        
        'data/tw_account_filter_selection_data.xml',

    ],
}

