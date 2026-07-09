{
    'name': "TW Account Period Fiscal Year",

    'summary': "Connecting Account Period to Fiscal Year",

    'description': """
        Connecting Account Period to Fiscal Year
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
    'depends': ['base', 'om_fiscal_year', 'tw_account_period'],

    # always loaded
    'data': [
        'views/tw_account_period_inherit_view.xml',
        'views/account_fiscal_year_inherit_view.xml',
        'views/account_move_inherit_view.xml',
    ],
}