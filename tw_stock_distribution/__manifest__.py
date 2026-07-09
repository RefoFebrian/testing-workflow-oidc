# -*- coding: utf-8 -*-
{
    'name': "TW Stock Distribution",

    'summary': "Module for managing and distributing stock efficiently",

    'description': """
    This module provides comprehensive tools for managing and distributing stock within an organization. It allows users to track inventory levels, manage stock movements, and ensure that stock is distributed efficiently across various locations. Key features include:

    - Real-time inventory tracking
    - Automated stock replenishment
    - Detailed reporting and analytics
    - Integration with other modules for seamless operations
    - User-friendly interface for easy management

    This module is designed to help businesses optimize their stock distribution processes, reduce waste, and improve overall efficiency.

    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Inventory',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','tw_sale','tw_menu','tw_selection','tw_stock','tw_purchase_order','tw_account_partner'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'data/tw_cron_data.xml',

        'views/tw_stock_distribution_view.xml',
        'views/tw_stock_distribution_update_date_view.xml',
        'views/tw_sale_order_inherit_view.xml',
        'views/tw_menu.xml',
    ],
    'application':True,
    'installable':True,
}

