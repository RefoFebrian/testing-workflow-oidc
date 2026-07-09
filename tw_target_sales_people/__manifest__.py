# -*- coding: utf-8 -*-
{
    'name': 'TW Target Sales People',

    'summary': 'Manage sales targets and daily sales targets',

    'description': """
        This module provides functionality to manage:
        - Sales people targets
        - Daily sales targets
        - Target upload via Excel
    """,

    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base', 'tw_base', 'tw_menu'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/tw_master_target_data.xml',
        'data/tw_category_target_data.xml',
        
        'views/tw_master_target_view.xml',
        'views/tw_target_sales_people_view.xml',
        'views/tw_target_daily_sales_view.xml',

        'wizard/tw_upload_target_sales_people_wizard_view.xml',
        'wizard/tw_upload_target_daily_sales_wizard_view.xml',

        'views/tw_menu.xml',
        
    ],
    
    'installable': True,
    'application': True,
}

