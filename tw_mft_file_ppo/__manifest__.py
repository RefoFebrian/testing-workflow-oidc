# -*- coding: utf-8 -*-
{
    'name': "TW MFT File PPO",

    'summary': "MFT File PPO",

    'description': """
        Generate data PPO for send to AHM
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
        'product',
        'stock',
        'hr',
        'tw_config_files',
        'tw_selection',
        'tw_branch',
        'tw_partner',
        'tw_nrfs',
        'tw_vehicle',
        'tw_localization',
        ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',
        
        'views/tw_mft_file_ppo_view.xml',
    ],
    'installable': True,
    'application': True,
}

