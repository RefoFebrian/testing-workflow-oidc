{
    "name": "Registration Document Handover Cancellation",
    "summary": "Registration Document Handover Request and Receive Cancellation Management",
    "description": """
        Registration Document Handover Cancellation
        ============================================
        
        This module provides functionality to manage registration document handover cancellations
        including both document requests and receipts within the Tunas Honda system.
        
        Key Features:
        * Cancel registration document handover requests and receipts
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
    "depends": [
        "base",
        "mail",
        "tw_base",
        "tw_menu",
        "tw_approval",
        "tw_branch",
        "tw_vehicle_document",
        "tw_cancellation",
        "tw_vehicle_document_handover",
        "tw_vehicle_document_cancel",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "security/ir_rule.xml",
        "security/res_groups_button.xml",
        "views/tw_registration_document_handover_cancel_views.xml",
        "views/tw_ownership_document_handover_cancel_views.xml",
        "views/tw_menu.xml",
    ],
    "demo": [],
    "images": [],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False
}
