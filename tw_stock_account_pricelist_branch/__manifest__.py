{
    # TODO : Might not be needed because of FIFO Valuation already handle this
    'name': "TW Stock Account Pricelist Branch",
    'summary': "Stock Account Pricelist Branch",

    'description': """
        Stock Account Pricelist Branch
    """,

    'license': 'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_suspend_security', 'tw_pricelist_branch', 'tw_stock_account'],

    # always loaded
    'data': [],
    'installable': True,
    'application': True,
}

