# -*- coding: utf-8 -*-
{
    'name': "TW Payment",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
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
    'depends': [
        'base', 
        'tw_base', 
        'tw_menu', 
        'tw_web', 
        'tw_branch', 
        'tw_account',  
        'account', 
        'account_payment', 
        'om_account_accountant', 
        'tw_selection', 
        'tw_sequence',
        'tw_account_filter',
        'tw_attachment',
        ],

    # always loaded
    'data': [
        # Security Data
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_button_groups.xml',
        'security/ir_rule.xml',
        
        # 
        'data/tw_account_data.xml',
        'data/tw_account_filter_selection_data.xml',


        # Base Payment View
        'views/tw_payment_view.xml',
        'views/tw_payment_line_view.xml',
        'views/tw_receive_payment_view.xml',

        # Customer View
        'views/tw_customer_payment_view.xml',

        # Supplier View
        'views/tw_supplier_payment_view.xml',
        
        # Invoice
        'views/tw_account_invoice_view.xml',

        # Config
        'views/tw_account_payment_method_view.xml',
        
        # Menu 
        'views/tw_payment_menu.xml',
        # Config
        'report/tw_report_template.xml',
        'report/tw_report_actions.xml',
        'report/tw_report_kwitansi_template.xml',
        'report/tw_report_kwitansi_actions.xml',
        'report/tw_customer_payment_report_template.xml',
        'report/tw_supplier_payment_report_template.xml',
    ],
    'assets': {
    'web.assets_backend': [
        'tw_payment/static/src/css/state.css',
    ],
},
}

