# -*- coding: utf-8 -*-
{
    'name': "TW MRP Bundling",

    'summary': "Enhances MRP capabilities with improved product bundling views and management.",

    'description': """
The TW MRP Bundling module is designed to enhance the manufacturing resource planning (MRP) capabilities within the Odoo ERP system. This module provides additional functionalities and views to streamline the bundling process of products. It aims to improve efficiency and accuracy in managing product bundles, ensuring that all components are correctly accounted for and assembled.

Key Features:
- Enhanced product bundling views
- Improved management of MRP processes
- Seamless integration with existing Odoo modules

This module is ideal for businesses looking to optimize their manufacturing processes and ensure accurate product bundling.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_mrp','mrp','tw_mrp_bom_product','tw_stock'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'wizard/tw_upload_serial_wizard_view.xml',
        'wizard/tw_bundling_production_report_view.xml',
        'views/tw_mrp_production_view.xml',
        'views/tw_mrp_view.xml',
        'views/tw_mrp_unbuild_view.xml',
        'views/tw_stock_lot_view.xml',
        'views/tw_menu.xml',
        'views/tw_stock_warehouse_view.xml',
        'views/tw_product_category_inherit_view.xml',
        'views/tw_mrp_workcenter_inherit_view.xml',
    ],
}

