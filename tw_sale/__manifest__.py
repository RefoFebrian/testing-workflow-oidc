# -*- coding: utf-8 -*-
{
    'name': "TW Sale",

    'summary': """
        TW Sale
        """,

    'description': """
        TW Sale 
        - Remove Unused Sale Menu
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'TW Sales/ TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'stock',
        'sale_stock',
        'sale_management',
        'sale_pdf_quote_builder',
        'tw_branch',
        'tw_selection',
        'spreadsheet_dashboard',
        'tw_print_counter',
        'tw_account_setting',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'security/ir_rule.xml',
        
        'report/tw_sale_order_report_template.xml',
        'report/tw_sale_order_report_view.xml',
        
        'views/tw_sale_order_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_menu_view.xml',
        'views/tw_branch_inherit_view.xml',
    ],

    'application':True,
    'installable':True,


    'external_dependencies': {},

    "post_init_hook": "_tw_sale_post_init",  
}