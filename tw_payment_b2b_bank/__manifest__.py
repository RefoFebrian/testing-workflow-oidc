{
    'name': "TW Payment B2B Bank",
    
    'summary': "Module integrations of Account Payment within B2B Bank",

    'description': """
        This module is integrate of Payment Approval module within B2B Bank module.
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
        'base',
        'tw_base',
        'tw_config_files',
        'tw_payment_approval',
        'tw_b2b_bank',
    ],

    # always loaded
    'data': [
        'data/payment_method_data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_payment_provider_inherit_view.xml',
        'views/tw_account_payment_inherit_view.xml',
        'views/tw_payment_transaction_inherit_view.xml',
    ],
}