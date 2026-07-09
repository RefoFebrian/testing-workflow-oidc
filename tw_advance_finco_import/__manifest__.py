{
    'name': "TW Advance Finco Import",

    'summary': "Module to import and manage finance company (finco) transaction data.",

    'description': """
        This module provides functionality to import finance company (finco) data into the system.
        It supports structured data imports, mapping, and validation to ensure accuracy and consistency.
        Useful for businesses working with financing or leasing partners, it helps streamline data entry,
        reduce manual processing, and maintain up-to-date finance records to become Customer Payment data of Finco.
        Ideal for accounting and finance teams that need efficient integration with external finance companies.
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
        'base',
        'tw_base',
        'tw_menu',
        'tw_payment',
        'tw_dealer_sale_order'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_advance_finco_import_view.xml',
        'views/tw_menu_view.xml',
    ],
}