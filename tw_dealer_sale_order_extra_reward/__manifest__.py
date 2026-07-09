{
    'name': "TW Dealer Sale Order Extra Reward",

    'summary': "Module of Dealer Sale Order using Extra Reward",

    'description': """
        Module of Dealer Sale Order using Extra Reward
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': "LGPL-3",
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_dealer_sale_order', 'tw_sales_program','tw_account_setting','tw_account'],

    # always loaded
    'data': [
        'data/data.xml',
        
        'views/tw_dealer_sale_order_inherit_view.xml',
        'views/tw_account_setting_inherit_view.xml',
    ],
}

