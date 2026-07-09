# -*- coding: utf-8 -*-
{
    'name': "TW Purchase Order Cancel",

    'summary': "Allows users to cancel purchase orders with proper validations.",

    'description': """
This module provides functionality to cancel purchase orders in Odoo. 
It ensures that proper validations are in place before a purchase order can be canceled, 
helping to maintain data integrity and avoid accidental cancellations. 
The module integrates seamlessly with existing Odoo modules such as 'account', 'tw_base', 
'tw_selection', and 'tw_account_period', ensuring compatibility and extended functionality.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','tw_base','tw_cancellation','tw_approval','tw_account_purchase','tw_account_setting'],

    # always loaded
    'data': [
        
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_purchase_order_cancel_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',
        
        'data/tw_cancellation_handler_data.xml'
    ],

}

