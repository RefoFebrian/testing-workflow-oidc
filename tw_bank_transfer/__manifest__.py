# -*- coding: utf-8 -*-
{
    'name': "TW Bank Transfer",

    'summary': "This module will be used to manage bank transfer process. "
               "On this module, you can create bank transfer and view bank transfer",

    'description': """
    This module will be used to manage bank transfer process. 
    On this module, you can create bank transfer and view bank transfer

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
    'depends': ['base','tw_base', 'tw_web', 'tw_selection','tw_petty_cash','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_group_button.xml',
        'security/ir_rule.xml',
        
        'report/tw_report_bank_transfer_template.xml',
        
        'views/tw_bank_transfer_view.xml',
        'views/tw_account_settings_view.xml',
        'views/tw_menu.xml',
    ]
}   

