{
    'name': "TW Payment Invoice",
    
    'summary': "Module to automate invoice payment creation with Manual Payment process, QRIS and Virtual Account support.",

    'description': """
            This module automates the creation and processing of payments directly especially Customer Payment (AR) from invoices.
        It supports multiple payment methods, including Manual, QRIS and Virtual Account (VA), 
        enabling seamless and flexible payment options for customers.
        Ideal for businesses that require efficient invoice-to-payment processing, reduced manual work,
        and support for modern digital payment methods.
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
        'tw_base',
        'tw_payment_astrapay',
        'tw_b2b_bank_bca_payment',
        'tw_work_order',
        'tw_dealer_sale_order',
    ],

    # always loaded
    'data': [
        'security/res_groups_button.xml',

        'views/tw_account_move_inherit_view.xml',
        'views/tw_work_order_inherit_view.xml',
        'views/tw_dealer_sale_order_inherit_view.xml',
    ],
}