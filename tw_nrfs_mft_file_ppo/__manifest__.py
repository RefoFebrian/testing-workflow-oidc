# -*- coding: utf-8 -*-
{
    'name': "TW NRFS - MFT File PPO",

    'summary': "NRFS Connected to MFT File PPO",

    'description': """
        NRFS Connected to MFT File PPO
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_nrfs',
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        
        'views/tw_nrfs_inherit_view.xml',
    ],
    'installable': True,
    'application': True,
}

