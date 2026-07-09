# -*- coding: utf-8 -*-
{
    'name': "TW Stock",

    'summary': "Stock",

    'description': """
        Stock
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
        'tw_branch',
        'stock',
        'stock_picking_batch',
        'account',
        'stock_account',
        'sale_stock',
        'purchase_stock',
        'stock_delivery',
        'tw_base',
        'tw_menu',
        'tw_selection',
        'tw_product',
        'tw_web'
    ],

    # always loaded
    'data': [
        'data/stock_location_type_nrfs_data.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        
        'views/tw_branch_inherit_view.xml',
        'views/tw_stock_location_view.xml',
        'views/tw_stock_picking_view.xml',
        'views/tw_stock_picking_in_view.xml',
        'views/tw_stock_picking_out_view.xml',
        'views/tw_stock_picking_batch_view.xml',
        'views/tw_stock_picking_batch_md_view.xml',
        'views/tw_stock_picking_batch_retail_view.xml',
        'views/tw_stock_picking_type_view.xml',
        'views/tw_stock_lot_view.xml',
        'views/tw_stock_move_view.xml',
        'views/tw_stock_move_line_view.xml',
        'views/tw_res_config_settings_views.xml',
        'views/tw_stock_quant_view.xml',
        'views/tw_selection_stock_location_view.xml',
        'views/tw_stock_route_view.xml',
        'views/tw_stock_rule_view.xml',
        'views/tw_stock_quality_check_incoming_view.xml',
        'views/tw_stock_picking_return_view.xml',
        
        # Menu
        'views/tw_stock_menu_view.xml',
        
        # Report
        'report/template/tw_stock_picking_list_report_template_view.xml',
        'report/tw_stock_picking_list_report_view.xml',
        'report/template/tw_stock_picking_travel_document_report_template_view.xml',
        'report/tw_stock_picking_travel_document_report_view.xml',
        'report/template/tw_stock_picking_batch_travel_document_report_template_view.xml',
        'report/tw_stock_picking_batch_travel_document_report_view.xml',
        'report/template/tw_stock_picking_goods_receipt_template_view.xml',
        'report/tw_stock_picking_batch_goods_receipt_view.xml',
        'report/template/tw_stock_picking_batch_bastk_report_template_view.xml',
        'report/tw_stock_picking_batch_bastk_report_view.xml',
    ],
    
    "installable": True,
	"application": True,
    "auto_install": False,
    "post_init_hook": "_tw_inventory_post_init",
}

