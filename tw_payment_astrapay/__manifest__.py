{
    'name': "TW Payment AstraPay",
    
    'summary': "Module integrations of AstraPay within Payment",

    'description': """
        Integrates payment processing with Odoo Invoices using AstraPay.
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
    ],

    # always loaded
    'data': [
        'data/payment_provider_data.xml',
        'data/account_payment_method_data.xml',
        # 'data/partner_data.xml',
        # 'data/partner_retail_data.xml',
    ],
}