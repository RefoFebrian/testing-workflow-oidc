# -*- coding: utf-8 -*-
{
    'name': "TW Payment Print Counter",

    'summary': "Added Report Printing Calculation Workflow and Reprint Reason to TW Payment module to be able to monitor printing history.",

    'description': """
    This module integrates the Print Counter with TW Payments to track the number of times a payment document has been printed. It ensures document control, prevents misuse, and maintains an accurate print history throughout the payment process.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_payment','tw_print_counter','tw_register_kwitansi'],

    # always loaded
    'data': [
        'views/tw_print_counter_wizard_view.xml',
        'views/tw_report_kwitansi_template_inherit.xml',
    ]
}

