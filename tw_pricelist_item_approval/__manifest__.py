# -*- coding: utf-8 -*-
{
    'name': "TW Pricelist Item Approval",

    'summary': "TW Pricelist Item Approval",

    'description': """
        Pricelist Item with Matrix Approval
    """,

    'author': "Tunas Honda",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Pricelist / TW Pricelist Item',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','product','tw_pricelist','tw_approval'],

    # always loaded
    'data': [  
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_product_pricelist_item_view.xml',
    ],
    
    "installable": True,
	"application": True,
    "auto_install": False,
}

