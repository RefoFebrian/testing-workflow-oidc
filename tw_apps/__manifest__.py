{
    'name': 'TW Apps',
    'version': '1.0',
    'license': 'LGPL-3',
    'summary': 'Manage App Versions',
    'description': """
        This module manages application versions and related configurations.
    """,
    'category': 'Technical',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'tw_base',
        'tw_menu',
        'tw_selection',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/tw_apk_type_data.xml',

        'views/tw_app_version_view.xml',
        'views/tw_master_app_type_view.xml',
        'views/tw_menu.xml',
    ],
    'application':True,
    'installable':True,
}