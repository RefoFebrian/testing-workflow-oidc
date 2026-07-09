# -*- coding: utf-8 -*-
{
    'name': "TW Pricelist Branch",

    'summary': "TW Pricelist Branch",

    'description': """
        Pricelist with Branch (Res Company with Parent)
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Pricelist Branch / TW Pricelist Branch',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_pricelist','tw_branch','tw_branch_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        
        'views/tw_pricelist_branch_view.xml',
    ],
}

