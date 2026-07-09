{
    'name': "TW B2B Bank BCA Payment",
    
    'summary': "Module integrations of B2B Bank Central Asia (BCA) within Bank Transfer and Payment",

    'description': """
        This module is integrate of B2B Bank Central Asia (BCA) module
        within Bank Transfer Approval module and Payment Approval module.
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
        'tw_payment_b2b_bank',
        'tw_b2b_bank_bca',
        'tw_bank_transfer_approval'
    ],

    # always loaded
    'data': [
        'data/payment_provider_data.xml',
        'data/account_payment_method_data.xml',
    ],
}