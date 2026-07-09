# -*- coding: utf-8 -*-
{
    'name': "Tw Dealer Sale Order Finco",

    'summary': "Manage retail sales with credit payment through finance companies.",

    'description': """
This module facilitates the management of retail sales where customers opt for credit payment 
using finance companies. It streamlines the process of integrating finance companies into 
the sales workflow, ensuring accurate tracking and management of credit-based transactions.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'tw_base', 'tw_dealer_sale_order','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'reports/tw_dealer_sale_order_invoice_report_inherit_template.xml',
        'reports/tw_dealer_sale_order_serah_bpkb_inherit_template.xml',

        'views/tw_partner_incentive.xml',
        'views/tw_dealer_sale_order_inherit_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        
        'wizard/tw_dealer_sale_order_report_wizard_inherit_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

