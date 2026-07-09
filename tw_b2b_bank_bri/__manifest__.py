{
    'name': "TW B2B Bank BRI",

    'summary': "Module for managing B2B banking transactions and integrations on Bank Rakyat Indonesia (BRI)",

    'description': """
        This module streamlines B2B banking operations by facilitating the management of bank transactions
        between businesses. It supports the generation of bank files for payments, integration with banking APIs,
        and automated reconciliation workflows. Ideal for finance departments to handle bulk transactions,
        vendor payments, and ensure secure, compliant, and efficient banking processes in a business-to-business context.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Accounting / TW Accounting',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'tw_bank_reconcile'
    ],

    # always loaded
    'data': [
        'data/data.xml',
        'data/tw_cron_data.xml',

        'views/tw_api_configuration_inherit_view.xml',
    ],
}