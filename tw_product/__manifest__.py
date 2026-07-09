# -*- coding: utf-8 -*-
{
    'name': "TW Product",

    'summary': "Products",

    'description': """
        Products
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Products / TW Products',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'product',
        'stock',
        'account',
        'tw_menu',
        'tw_selection'
        ],

    # always loaded
    'data': [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        
        "data/tw_data_account_product_category.xml",
        "data/tw_data_product_category.xml",
        
        "views/tw_product_template_view.xml",
        "views/tw_product_attribute_view.xml",
		"views/tw_product_variants_view.xml",
        "views/tw_product_type_view.xml",
        "views/tw_product_category_view.xml",
        "views/tw_unit_parts_view.xml",
        "views/tw_menu_product.xml",
        
        
    ],
    'demo': [
        # 'demo/tw_data_product_attribute.xml',
        # 'demo/tw_data_product_category.xml',
        # 'demo/tw_data_product_series.xml',
        # 'demo/tw_data_product_type.xml',
    ],
    "installable": True,
	"auto_install": False,
	"application": True,
}

