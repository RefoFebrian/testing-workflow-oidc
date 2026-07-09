# -*- coding: utf-8 -*-
{
    'name': "TW Advance Payment",

    'summary': "TW Advance Payment",

    'description': """
TW Advance Payment
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
    'depends': ['base','tw_base','tw_selection','tw_payment','tw_account_setting','tw_attachment'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'data/ir_configparameter_data.xml',
        'security/ir_rule.xml',

        'views/tw_advance_payment_view.xml',
        'views/tw_account_setting_view.xml',
        'views/res_config_settings_view.xml',
        'views/tw_menu.xml'
    ],
}

