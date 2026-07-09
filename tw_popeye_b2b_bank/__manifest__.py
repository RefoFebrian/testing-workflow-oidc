{
    'name': "TW Popeye B2B Bank",

    'summary': "Module for managing Popeye Payment Gateway to integrate on Bank modules",

    'description': """
        This module provides to integrate the external Popeye payment system and bank modules, e.g. BCA, BRI, etc.
        It allows sending statement of mutation bank from Popeye payment system.
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
        'tw_popeye',
        'tw_b2b_bank_bca'
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',
        
        'views/tw_bank_mutasi_inherit_view.xml'
    ],
}