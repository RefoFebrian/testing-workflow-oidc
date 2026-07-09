# -*- coding: utf-8 -*-
{
    'name': "TW MRP Extras",

    'summary': "Extends MRP functionalities with additional attributes and operations for better production control",

    'description': """
    This module extends the Manufacturing Resource Planning (MRP) functionalities in Odoo by adding specific extras types. It allows users to define and manage additional attributes and operations related to the manufacturing process, providing more flexibility and control over production workflows.
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
    'depends': ['base','tw_base','tw_mrp','tw_product','tw_mrp_bom_product'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/product_category.xml',
        'views/tw_product_view.xml',
        'views/tw_mrp_view.xml',
        'views/tw_menu.xml',
    ],
}

