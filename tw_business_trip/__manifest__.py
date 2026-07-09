# -*- coding: utf-8 -*-
{
    'name': "TW Business Trip",

    'summary': "Module of Business Trip",

    'description': """
    This module is used by internal Main Dealer to manage business trip.
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
    'depends': ['base','tw_base','tw_selection','tw_approval','tw_attachment','tw_payment_request','tw_settlement'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'reports/reports.xml',

        'views/tw_business_trip_view.xml',
        'views/tw_business_trip_plafon_view.xml',
        'views/tw_master_ttd_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',

        'reports/tw_business_trip_print_view.xml'
    ],

    'external_dependencies': {
        'python': ['PyPDF2'],
    },
}

