# -*- coding: utf-8 -*-
{
    'name': 'TW Consolidate Invoice',
    'summary': 'Module to consolidate supplier invoices',
    'description': """
        Module to consolidate supplier invoices with detailed lines.
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'TW',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base',
                'account',
                'stock',
                'product',
                'uom',
                'purchase',
                'purchase_mrp',
                'tw_account',
                'tw_stock',
                'tw_stock_extras',
                'tw_menu',
                'tw_selection',
                'tw_stock_stored',
                ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/tw_consolidate_invoice_view.xml',
        'views/tw_purchase_order_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}