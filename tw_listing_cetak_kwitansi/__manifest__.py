{
    'name': "TW Listing Cetak Kwitansi",

    'summary': "Module to generate, print, and manage receipt documents (kwitansi).",

    'description': """
        This module provides functionality to create, list, and print official receipt documents (kwitansi).
        It helps businesses generate standardized receipts for transactions, maintain organized records,
        and ensure professional documentation for customers or partners.
        Ideal for finance and administrative teams to track issued receipts and simplify reporting.
""",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_menu',
        'tw_selection',
        'tw_branch_setting',
        'tw_account',
        'web_report'
    ],

    # always loaded
    'data': [
        "data/tw_list_cetak_kwt_trx_option_data.xml",

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        
        'report/template/tw_listing_cetak_kwitansi_print_pdf_report_template_view.xml',
        'report/tw_listing_cetak_kwitansi_report_view.xml',
        'report/tw_listing_cetak_kwitansi_print_pdf_report_view.xml',

        'views/tw_listing_cetak_kwitansi_view.xml',
        'views/tw_menu_view.xml',
    ],
}