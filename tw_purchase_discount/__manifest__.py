# -*- coding: utf-8 -*-
{
    'name': "TW Purchase Discount",

    'summary': "Module to manage and apply discounts on purchase orders effectively",

    'description': """
This module provides functionality to manage and apply discounts on purchase orders in an efficient manner. 
It allows users to configure discount rules, apply them automatically or manually, and track the impact of discounts 
on purchase order totals. The module is designed to streamline the purchasing process and improve cost management 
for businesses.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'TW Purchase / TW Purchase',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': ['base', 'purchase', 'tw_base', 'tw_purchase_order', 'tw_account_setting'],

    'data': [
        'security/res_groups.xml',
        'views/tw_purchase_order_discount_view.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}

