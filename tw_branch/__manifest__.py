# -*- coding: utf-8 -*-
{
    'name': "TW Branch",

    'summary': "Master Branch",

    'description': """
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr',
        'tw_localization',
        'tw_partner',
        'tw_selection',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'data/branch_type_data.xml',
        'data/master_branch_category.xml',
        'data/master_dealer_class.xml',
        # 'data/res_branch.xml', #? : Hidupkan sesuai kebutuhan saja, untuk prod tidak perlu 


        'views/res_branch_view.xml',
        'views/res_users_inherit_view.xml',
        'views/tw_branch_partner_views.xml',
    ],

    'application':True,
    'installable':True,

    'demo': [
        # 'demo/res_branch.xml',
    ],
}

