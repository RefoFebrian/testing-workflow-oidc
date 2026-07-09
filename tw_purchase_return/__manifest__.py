# -*- coding: utf-8 -*-
{
    'name': "TW Purchase Return",
    'summary': """
        TW Purchase Return Management
    """,
    'description': """
        This module allows you to manage purchase returns with the following features:
        - Create and manage purchase returns
        - Link to original purchase orders
        - Generate return pickings
        - Track return status
    """,
    'author': "Tunas Group",
    'website': "https://www.tunasgroup.com",
    'category': 'Purchases',
    'version': '1.0',
    'depends': [
        'base',
        'sale',
        'product',
        'stock',
        'sale_stock',
        'tw_branch',
        'tw_selection',
        'tw_purchase_order',
        'tw_consolidate_invoice',
        'tw_account_purchase',
        'tw_account_setting',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rules.xml',
        'views/tw_purchase_return_views.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/stock_warehouse_views.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
