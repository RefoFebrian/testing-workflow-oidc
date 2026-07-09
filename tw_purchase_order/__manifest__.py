# -*- coding: utf-8 -*-
{
    'name': "TW Purchase Order",

    'summary': "Enhancement of Purchase Order functionality for our automotive company",

    'description': """
    This module provides enhancements to the standard Purchase Order functionality in Odoo, tailored specifically for the needs of our automotive company. It includes additional fields, improved workflows, and custom reports to streamline the purchasing process and ensure better tracking and management of purchase orders. Key features include:

    - Custom fields for automotive-specific data
    - Enhanced approval workflows
    - Integration with other modules such as inventory and accounting
    - Customizable reports for better insights into purchasing activities
    - User access controls to ensure data security and integrity

    These enhancements are designed to improve efficiency, accuracy, and visibility in the purchasing process, ultimately supporting better decision-making and operational performance.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in the modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Purchase / TW Purchase',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'account', 
        'purchase', 
        'purchase_stock',
        'stock', 
        'tw_base', 
        'tw_selection', 
        'tw_menu', 
        'tw_branch', 
        'tw_branch_setting', 
        'tw_account_branch', 
        'tw_stock',
        'tw_stock_purchase',
        ],

    # always loaded
    'data': [
        'data/master_data_selection.xml',
        'data/master_data_po_type.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'views/tw_purchase_order_type_view.xml',
        'views/tw_purchase_order_view.xml',
        'views/tw_purchase_order_line_view.xml',
        'views/tw_purchase_menu_view.xml',
        'views/tw_branch_setting_inherit_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tw_purchase_order/static/src/components/**/*',
        ],
    },
}

