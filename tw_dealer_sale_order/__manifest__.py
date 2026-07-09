# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order",

    'summary': "Module for managing and handling retail sales operations effectively.",

    'description': """
        This module is designed to streamline and manage retail sales processes, 
        providing tools for invoicing, reporting, and integration with other modules 
        to ensure smooth sales operations.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'account', 
        'analytic', 
        'product', 
        'sale', 
        'sales_team', 
        'uom',
        'tw_base', 
        'tw_branch', 
        'tw_menu', 
        'tw_selection', 
        'tw_hr', 
        'tw_sequence', 
        'tw_stock',
        'tw_pricelist', 
        'tw_product',
        'tw_account_setting',
        'tw_web'
        ],

    # always loaded
    'data': [
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'wizard/tw_dealer_sale_make_invoice_advance_views.xml',
        
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_dealer_sale_order_line_view.xml',
        'views/tw_dealer_sale_order_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_stock_picking_inherit_view.xml',

        'wizard/tw_dealer_sale_order_report_wizard_view.xml',
        'wizard/tw_dealer_sale_order_pelunasan_leasing_bank_view.xml',
        'wizard/tw_dealer_sale_order_surat_kuasa_view.xml',
        
        'report/tw_dealer_sale_order_dp_po_report_view.xml',
        'report/tw_dealer_sale_order_pelunasan_leasing_report_view.xml',
        'report/tw_dealer_sale_order_serah_bpkb_report_view.xml',
        'report/tw_dealer_sale_order_invoice_report_view.xml',
        'report/tw_dealer_sale_order_surat_kuasa_report_view.xml',
        'report/tw_dealer_sale_order_data_consumen_report_view.xml',
        'report/tw_dealer_sale_order_penjualan_report_view.xml',
        'report/tw_dealer_sale_order_penjualan_direct_gift_report_view.xml',
        'report/tw_dealer_sale_order_cod_settlement_report_view.xml',

        'report/template/tw_dealer_sale_order_dp_po_template.xml',
        'report/template/tw_dealer_sale_order_pelunasan_leasing_template.xml',
        'report/template/tw_dealer_sale_order_serah_bpkb_template.xml',
        'report/template/tw_dealer_sale_order_invoice_report_template.xml',
        'report/template/tw_dealer_sale_order_surat_kuasa_template.xml',
        'report/template/tw_dealer_sale_order_cod_settlement_template.xml',

        'views/tw_menu_item.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}

