# -*- coding: utf-8 -*-
{
    'name': "TW P2P MFT UPO",

    'summary': "Module for creating UPO files using b2b_file and p2p modules",

    'description': """
    This module facilitates the creation of UPO (Purchase Order) files and integrates with the b2b_file and p2p modules to streamline the process. It ensures seamless data handling and efficient file management for business-to-business transactions.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base', 'tw_base','tw_p2p','tw_b2b_file'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_p2p_purchase_order_view.xml',
    ],
}

