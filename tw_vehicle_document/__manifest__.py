{
    'name': "TW - Vehicle Document Management",
    'summary': "Management of Vehicle Documents (STNK, BPKB, etc)",
    'description': """
        This module handles the complete management of vehicle documents including:
        - Document requests
        - Document receiving
        - Document tracking
        - Document status updates
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'Inventory/Inventory',
    'version': '1.0.0',
    'license': 'LGPL-3',
    
    # Dependencies
    'depends': [
        'base',
        'tw_base',
        'stock',
        'tw_stock',
        'tw_partner',
        'tw_partner_cdb',
        'tw_dealer_sale_order_bbn',
        'tw_dealer_sale_order_finco',
    ],

    # Data files to load
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        # Load views before menu
        'views/tw_vehicle_document_outstanding_views.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_vehicle_document_request_views.xml',
        'views/tw_vehicle_document_receive_views.xml',
        'views/tw_udstk_views.xml',
        'views/tw_partner_cdb_inherit_views.xml',
        'views/tw_menu.xml',  # Menu should be loaded last
    ],
    
    # Auto-install
    'auto_install': True,
    'installable': True,
    'application': True,
}