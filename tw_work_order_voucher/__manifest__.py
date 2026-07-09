# -*- coding: utf-8 -*-
{
    'name': "TW Work Order Voucher",

    'summary': "TW Work Order Voucher",

    'description': """
        TW Work Order Voucher
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'tw_base',
        'tw_branch',
        'tw_work_order',
        'tw_sales_voucher',
        'tw_account',
        'tw_account_setting',
        'tw_stock',
        'tw_payment',
        'tw_payment_approval',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/tw_work_order_inherit_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'report/tw_wo_invoice_print_inherit_view.xml',
    ],
}

