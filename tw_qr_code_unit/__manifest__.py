# -*- coding: utf-8 -*-
{
    'name': "TW Print QR Code Unit",

    'summary': "Print QR Code Unit",

    'description': """
        Print QR Code Unit
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
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'tw_menu',
        'tw_stock'
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_qr_code_unit_view.xml',
        'views/tw_print_generate_qr_code_view.xml',

        # Wizards
        'wizards/tw_generate_qr_code_unit_wizard_view.xml',

        # Report
        'report/template/tw_print_qr_code_unit_template_view.xml',
        'report/tw_print_qr_code_unit_view.xml',
        'report/tw_report_qr_code_unit_wizard_view.xml',
        
        # Menu
        'views/tw_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}

