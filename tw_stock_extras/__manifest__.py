# -*- coding: utf-8 -*-
{
    'name': "TW Stock Extras",

    'summary': "Enhances stock management with custom views and templates",

    'description': """
Long description of module's purpose
    This module, `tw_stock_extras`, is designed to extend the stock management capabilities of Odoo. It provides additional features and functionalities to enhance the stock management process, making it more efficient and user-friendly. The module includes custom views and templates to better suit the specific needs of the business. It is intended for companies looking to optimize their inventory management and streamline their stock operations.
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
    'depends': [
        'base',
        'tw_base',
        'tw_stock',
        'tw_stock_inbound',
        'tw_mrp',
        'tw_mrp_extras',
        'tw_expedition_apps',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_stock_picking_batch_inherit_view.xml',
        'views/tw_stock_picking_inherit_view.xml',
        'views/tw_monitoring_expedition_apps_inherit_view.xml',
    ],
}
