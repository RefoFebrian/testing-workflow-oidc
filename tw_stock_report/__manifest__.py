{
    'name': "TW Report Inventory",

    'summary': "Comprehensive inventory reporting module with advanced filtering and Excel export, designed to support effective stock control across branches and teams.",

    'description': """
        This module provides detailed inventory reporting capabilities. 
        It supports filtering by branch, product, category, date, and other criteria. 
        Reports can be exported to Excel format. 
        It is highly useful for warehouse teams, auditors, management, and operational staff for effective stock control and decision-making.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Report / TW Report',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'stock', 
        'product', 
        'tw_base',
        'tw_branch',
        'tw_product',
        'tw_stock',
        'tw_stock_location_btl',
        'tw_menu',
        'tw_selection',
        'tw_purchase_order',
        'tw_dealer_sale_order',
        'tw_consolidate_invoice',
        'tw_mutation',
        'web_report',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_nrfs_report_view.xml',
        'views/tw_stock_movement_report_view.xml',
        'views/tw_stock_picking_report_view.xml',
        'views/tw_stock_inbound_report_view.xml',
        'views/tw_stock_report_view.xml',
        'views/tw_travel_document_report_view.xml',
        'views/tw_po_supply_sparepart_report_view.xml',
        'views/tw_stock_available_report_view.xml',
        'views/tw_menu_view.xml',
    ],
}

