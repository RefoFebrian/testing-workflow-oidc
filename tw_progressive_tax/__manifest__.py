# -*- coding: utf-8 -*-
{
    'name': "TW Progressive Tax",

    'summary': "TW Progressive Tax",

    'description': """
        TW Progressive Tax
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
        'stock',
        'account',
        'tw_menu',
        'tw_branch_setting',
        'tw_birojasa_billing_process',
        'tw_vehicle_registration_process'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_progressive_tax_view.xml',
        'views/tw_menu.xml',
        'views/tw_account_setting_inherit_view.xml',
    ],
}

