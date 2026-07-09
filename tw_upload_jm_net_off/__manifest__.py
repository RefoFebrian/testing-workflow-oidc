# -*- coding: utf-8 -*-
{
    'name': "TW Upload JM Net Off",

    'summary': "TW Upload JM Net Off",

    'description': """
        TW Upload JM Net Off
        - Provide import/export functionality for JM Net Off values
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'TW Sales / TW Sales',
    'version': '0.2',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_journal_memorial',
        'tw_net_off',
    ],
    
    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/tw_journal_memorial_upload_views.xml',
        'views/tw_net_off_upload_views.xml',
        'views/tw_menu_views.xml',
    ],
    'installable': True,
    'application': True,
}

