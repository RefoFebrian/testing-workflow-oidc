# -*- coding: utf-8 -*-
{
    'name': "TW DGI Inbound",

    'summary': "DGI Integration - Unit & Part Inbound (Purchase Order)",

    'description': """
        DGI Integration module for syncing Purchase Order data from Main Dealer.
        Supports:
        - UINB (Unit Inbound): Sync unit purchase orders with vehicle details
        - PINB (Part Inbound): Sync sparepart purchase orders with part details
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'TW Purchase / TW Purchase',
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',

    'depends': [
        'tw_dgi',
        'tw_purchase_order',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/tw_endpoint_dgi_uinb_data.xml',
        'data/tw_mapping_dgi_uinb_data.xml',
        'data/tw_endpoint_dgi_pinb_data.xml',
        'data/tw_mapping_dgi_pinb_data.xml',
        'data/tw_compile_output_template_data.xml',
        'wizards/tw_dgi_uinb_wizard_view.xml',
        'wizards/tw_dgi_pinb_wizard_view.xml',
        'wizards/tw_dgi_info_wizard_inherit_view.xml',
        'views/tw_purchase_order_inherit_view.xml',
        'views/tw_branch_setting_inherit_view.xml',
        'views/tw_stock_picking_inherit_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
