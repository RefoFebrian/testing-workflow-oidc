# -*- coding: utf-8 -*-
{
    'name': "TW Pricelist",

    'summary': "TW Pricelist",

    'description': """
        Pricelist
    """,

    'author': "Tunas Honda",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Pricelist / TW Pricelist',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'product',
        'base_suspend_security',
        'tw_base',
        'tw_menu',
        'tw_selection',
        'tw_partner',
        'tw_area'
    ],

    # always loaded
    'data': [  
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_product_pricelist_item_view.xml',
        'views/tw_product_pricelist_version_view.xml',
        'views/tw_product_pricelist_view.xml',
        'views/tw_product_template_view.xml',
        'views/tw_product_category_view.xml',
        'views/res_config_settings_view.xml',
        'views/tw_partner_view.xml',
        'views/tw_selection_pricelist_category_view.xml',

        'views/tw_pricelist_menus.xml',
        
        'views/tw_upload_pricelist_version_view.xml',

        # 'data/res_partner_data.xml',
        # 'data/tw_selection_data.xml',
        # 'data/res_config_settings_data.xml',
    ],
    
    "installable": True,
	"application": True,
    "auto_install": False,
    "post_init_hook": '_tw_pricelist_post_init', 
}

