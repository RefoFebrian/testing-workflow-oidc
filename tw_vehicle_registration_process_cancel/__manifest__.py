{
    "name": "Vehicle Registration Process Cancel",
    "summary": """
        Vehicle Registration Process Cancellation
    """,
    "description": """
        Handle cancellation of vehicle registration process
    """,
    "author": "Tunas Honda",
    "website": "https://www.honda-ku.com",
    "category": "Document Handling",
    "version": "18.0.1.0.0",
    "depends": [
        "base",
        "mail",
        "tw_base",
        "tw_menu",
        "tw_approval",
        "tw_branch",
        "tw_cancellation",
        "tw_vehicle_registration_process",
        "tw_vehicle_document",
        "tw_vehicle_document_cancel",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "security/res_groups_button.xml",
        "security/ir_rule.xml",
        
        "views/tw_vehicle_process_stnk_cancel_views.xml",
        "views/tw_menu.xml",
    ],
    "demo": [],
    "images": [],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False
}
