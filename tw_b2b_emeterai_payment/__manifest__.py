{
    'name': "TW Payment E-Meterai",

    'summary': "Module to manage electronic stamp duty (e-Meterai) for Payments (HL and AR) Kwitansi documents.",

    'description': """
        Module to manage electronic stamp duty (e-Meterai) for Payments (HL and AR) Kwitansi documents.
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
        'tw_b2b_emeterai',
        'tw_payment',
    ],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        
        'views/tw_customer_payment_inherit_view.xml',
        'views/tw_receive_payment_inherit_view.xml',
    ],
}