{
    "name": "Vehicle Document Cancellation",
    "summary": "Vehicle Document Request and Receive Cancellation Management",
    "description": """
        Vehicle Document Cancellation
        =============================
        
        This module provides functionality to manage vehicle document cancellations
        including both document requests and receipts within the Tunas Honda system.
        
        Key Features:
        * Cancel vehicle document requests and receipts
        * Track cancellation status and history
        * Maintain audit trails for cancelled documents
        * Integration with stock and inventory management
        * Multi-company and multi-branch support
    """,
    "author": "Tunas Honda",
    "company": "PT Tunas Dwipa Matra",
    "maintainer": "IT Department",
    "website": "https://www.honda-ku.com",
    "category": "Document Handling",
    "version": "1.0.0",
    "license": "LGPL-3",
    
    # Dependencies
    "depends": [
        "base",
        "stock",
        "tw_base",
        "tw_menu",
        "tw_cancellation",
        "tw_approval",
        "tw_vehicle_document"
    ],
    
    # Data files to load
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "security/res_groups.xml",
        "security/res_groups_button.xml",
        
        # Views
        "views/tw_vehicle_document_request_cancel_views.xml",
        "views/tw_vehicle_document_receive_cancel_views.xml",
        "views/tw_menu.xml",
    ],
    
    # Demo data (if any)
    "demo": [],
    
    # Module installation options
    "installable": True,
    "application": False,
    "auto_install": True,
}
