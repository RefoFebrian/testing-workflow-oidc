{
    'name': "TW Bank Reconcile",

    'summary': "Module for streamlined bank statement reconciliation in accounting processes.",

    'description': """
        This module facilitates efficient reconciliation of bank statements with accounting records.
        It enables users to import bank statements, match transactions automatically or manually,
        and quickly identify discrepancies. Designed to simplify and accelerate the reconciliation process,
        it helps ensure accuracy in financial reporting and reduces manual accounting errors.
        Ideal for accounting teams seeking to maintain up-to-date and reliable financial records.
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
        'account',
        'tw_base',
        'tw_menu',
        'tw_account',
        'tw_b2b_bank',
        'tw_bank_transfer',
        'web_report',
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
		'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'report/tw_bank_reconcile_report_view.xml',
        'report/tw_bank_reconcile_mutasi_report_view.xml',

        'views/tw_bank_reconcile_view.xml',
        'views/tw_bank_mutasi_view.xml',
        'views/tw_export_bank_mutasi_view.xml',
        'views/tw_import_bank_mutasi_view.xml',
        'views/tw_menu_view.xml',
    ],
}