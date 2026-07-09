# -*- coding: utf-8 -*-
{
    'name': "TW Work Order Cancel",

    'summary': "Module to manage and handle work order cancellations effectively.",

    'description': """
This module provides functionality to manage the cancellation of work orders in Odoo. 
It ensures proper handling of work order cancellations, maintaining data integrity and providing 
necessary tools for users to process cancellations efficiently. Key features include:
- Streamlined cancellation process for work orders.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': [
        'base', 
        'tw_base', 
        'tw_cancellation', 
        'tw_work_order', 
        'tw_approval', 
        'tw_account_setting'
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'views/tw_work_order_cancel_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',
        'data/tw_cancellation_handler_data.xml',

        'report/tw_work_order_cancel_print.xml',
        'report/tw_work_order_cancel.xml',
    ],
}

