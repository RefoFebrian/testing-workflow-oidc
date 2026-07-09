{
    "name": "TW Petty Cash",
    "summary": """
        Petty cash in, out and reimbursement
    """,
    "description": """
    """,
    "author": "Tunas Honda",
    "website": "https://www.honda-ku.com",
    "category": "Accounting/Finance",
    "version": "18.0.1.0.0",
    "depends": [
        "account",
        "hr",
        "rest_api",
        "tw_base",
        "tw_api",
        "tw_web",
        "tw_menu",
        "tw_account_setting",
        "tw_approval",
        "tw_branch",
        "tw_account_period",
        "tw_account_filter",
    ],
    "data": [
        "security/res_groups.xml",
        "security/res_groups_button.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "report/tw_petty_cash_out_report_view.xml",
        "report/tw_reimburse_petty_cash_report_view.xml",
        "views/tw_petty_cash_out_views.xml",
        "views/tw_petty_cash_in_views.xml",
        "views/tw_reimbursement_petty_cash_views.xml",
        "views/tw_petty_cash_type_views.xml",
        "views/tw_account_setting_view.xml",
        "views/tw_menu.xml",
        "data/tw_account_filter_selection_data.xml",
    ],
    "demo": [

    ],
    "images": [

    ],
    "license": "LGPL-3",
}
