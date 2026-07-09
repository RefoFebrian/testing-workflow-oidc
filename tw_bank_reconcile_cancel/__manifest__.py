{
    'name': "TW Bank Reconcile Cancel",

    'summary': "Module for cancel reconciliation of bank reconcile in accounting processes.",

    'description': """
        This module facilitate to cancel the data of bank reconcile that has been wrong data.
        Then Bank Statement that already cancel could be reconciliation process again.
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
        'tw_bank_reconcile',
        'tw_approval'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
		'security/res_groups_button.xml',

        'views/tw_bank_reconcile_cancel_view.xml',
        'views/tw_menu_view.xml',
    ],
}