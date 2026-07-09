# -*- coding: utf-8 -*-
{
    'name': "TW Account Asset Management",

    'summary': "Manage and track company assets efficiently.",

    'description': """
        This module provides comprehensive management and tracking of company assets. It allows users to record asset details, categorize assets, and track their depreciation over time. Key features include:

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
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base', 'om_account_asset'],

    # always loaded
    'data': [
        'views/tw_inherit_account_asset_view.xml'
    ],
}