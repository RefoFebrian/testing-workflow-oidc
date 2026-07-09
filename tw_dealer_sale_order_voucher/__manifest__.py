# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order Voucher",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base', 'tw_dealer_sale_order', 'tw_sales_program', 'tw_sales_voucher','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_account_setting_inherit_view.xml',
        'views/tw_dealer_sale_order_voucher_view.xml',
        'report/template/tw_dealer_sale_order_invoice_report_inherit_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

