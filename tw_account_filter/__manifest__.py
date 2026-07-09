{
    "name": "TW Account Filter",
    "version": "1.0",
    "author": "Tunas Honda",
    "website": "https://www.tunasgroup.com",
    "license": "LGPL-3",
    "category": "Accounting/Accounting",
    "summary": "Account Filter Module",
    "description": """
        This module provides account filtering functionality.
    """,
    "depends": [
        "base",
        "account",
        "tw_branch",
        "tw_menu",
    ],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "data/tw_account_filter_selection_data.xml",
        "views/tw_account_filter_views.xml",
        "views/tw_menu.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
