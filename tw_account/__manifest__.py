# -*- coding: utf-8 -*-
{
    'name': "TW Account",

    'summary': "Account",

    'description': """
        Account
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','tw_base','tw_selection','tw_product'],

    # always loaded
    'data': [
        'data/tw_account_move_type_data.xml',
        'data/tw_account_tax_group.xml',
        'data/tw_account_tax_pph.xml',
        'security/res_groups.xml',
        'security/res_button_groups.xml',
        'security/ir.model.access.csv',

        'views/inherit_partner_property_view.xml',
        'views/tw_account_journal_view.xml',
        'views/tw_account_move_view.xml',
        'views/tw_account_move_line_view.xml',
        'views/tw_account_account_inherit_view.xml',
        'views/tw_account_tax_inherit_view.xml',
        'views/tw_res_bank_view.xml',
        'views/tw_res_partner_bank_view.xml',
        'views/tw_menu.xml',

        'report/template/tw_account_move_report_template.xml',
        'report/tw_account_move_report_view.xml',
    ],
    'installable': True,
    'application': True,
}

