# -*- coding: utf-8 -*-
{
    'name': "TW Asset Management",

    'summary': "Manage and track company assets efficiently.",

    'description': """
        This module provides asset management and tracking of company assets. It allows users to record asset details, categorize assets, and track their depreciation over time. Key features include:

        - Asset Registration: Easily register new assets with detailed information such as purchase date, cost, and asset category.
        - Depreciation Management: Automatically calculate and record asset depreciation using various methods.
        - Asset Categorization: Organize assets into categories for better management and reporting.
        - Asset Disposal: Manage the disposal of assets and record any gains or losses.
        - Reporting: Generate detailed reports on asset values, depreciation, and asset movements.
        - Security: Define user roles and permissions to control access to asset information.

        This module integrates seamlessly with other Odoo modules to provide a complete solution for managing company assets.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.0.6',
    'license':'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'purchase',
        'stock',
        'tw_base',
        'tw_product',
        'om_account_asset',
        'tw_purchase_order',
        'tw_account_setting',
        'tw_attachment',

    ],
    
    'data': [
        'data/tw_product_category.xml',
        'data/tw_stock_location.xml',
        'data/tw_selection.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/tw_prepaid_asset_security.xml',
        'security/ir_rule.xml',

        'views/tw_account_asset_view.xml',
        'views/tw_prepaid_asset_views.xml',
        'views/tw_purchase_order_view.xml',
        'views/tw_product_template_view.xml',
        'views/tw_product_variant_view.xml',
        'views/tw_good_receive_view.xml',
        'views/tw_account_asset_category_view.xml',
        'views/tw_good_receive_collecting_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_stock_location_view.xml',
        'views/tw_asset_acquisition_view.xml',

        'views/tw_menu.xml'
    ],

    'pre_init_hook': 'pre_init_hook',
    'uninstall_hook': 'uninstall_hook',
}

