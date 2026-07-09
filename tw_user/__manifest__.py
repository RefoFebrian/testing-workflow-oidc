# -*- coding: utf-8 -*-
{
    'name': "TW User",
    'summary': "User Management",
    'description': """
        User Management with custom access control
    """,
    'author': "Tunas Group",
    'license': 'LGPL-3',
    'category': 'TW Base/TW Base',
    'version': '0.1',
    'depends': [
        'base',
        'tw_base'
    ],
    'data': [
        'security/res_groups.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
