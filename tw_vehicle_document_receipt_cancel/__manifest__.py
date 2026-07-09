{
    # Basic Information
    'name': 'TW Vehicle Document Receipt Cancellation',
    'version': '1.0.1',
    'category': 'Showroom/Vehicle',
    'summary': 'Handle cancellation of vehicle document receipts (STNK/BPKB)',
    'description': """
        Vehicle Document Receipt Cancellation
        ============================================
        
        This module provides functionality to cancel vehicle document receipts (STNK/BPKB)
        with proper state management and approval workflow.
        
        Features:
        - Cancellation request for STNK and BPKB receipts
        - Multi-level approval workflow
        - Integration with vehicle document management
        - Security and access control
    """,
    
    # Author Information
    'author': 'Tunas Honda',
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',
    
    # Dependencies
    'depends': [
        # Odoo Core
        'base',
        'mail',
        
        # Tunas Modules
        'tw_base',
        'tw_menu',
        'tw_approval',
        'tw_vehicle_document_receipt',
        'tw_vehicle_document',
        'tw_cancellation',
        'tw_vehicle_document_cancel',
    ],
    
    # Data Files
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        
        # Views
        'views/tw_vehicle_document_receipt_cancel_views.xml',
        'views/tw_vehicle_ownership_receipt_cancel_views.xml',
        'views/tw_menu.xml',
    ],
    
    # Module Configuration
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    
}
