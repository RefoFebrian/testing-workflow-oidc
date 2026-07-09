# -*- coding: utf-8 -*-
{
    'name': "TW P2P",

    'summary': "P2P Purchase Order from AHM to Main Dealer",

    'description': """
P2P Purchase Order from AHM to Main Dealer
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Purchase / TW Purchase',
    'application': True,
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_menu','tw_stock','tw_selection','tw_approval','tw_purchase_order','tw_product','tw_config_files','tw_stock_distribution','tw_stock', 'tw_web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        
        'wizard/tw_p2p_export_import_wizard.xml',
        'wizard/tw_p2p_product_import_wizard.xml',

        'views/tw_p2p_config_view.xml',
        'views/tw_p2p_category_fix_order_view.xml',
        'views/tw_p2p_periode_view.xml',
        'views/tw_p2p_product_view.xml',
        'views/tw_p2p_puchase_order_view.xml',
        'views/tw_purchase_order_inherit_view.xml',
        
        'report/template/tw_p2p_purchase_order_template.xml',
        'report/tw_p2p_purchase_order_actions.xml',
        
        'views/tw_menu_view.xml',
    ],
}

