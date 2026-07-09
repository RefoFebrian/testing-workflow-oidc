# -*- coding: utf-8 -*-
{
    'name': "TW Pricelist BBN",

    'summary': "TW Pricelist BBN",

    'description': """
        TW Pricelist BBN
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_area','tw_pricelist','tw_pricelist_branch', 'tw_branch_setting'],

    # always loaded
    'data': [
        'data/plate_type_data.xml',
        
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_branch_setting_inherit_view.xml',
        'views/tw_product_pricelist_item_inherit_view.xml',
    ],
}

