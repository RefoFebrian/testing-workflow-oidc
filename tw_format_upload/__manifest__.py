# -*- coding: utf-8 -*-
{
    'name': "TW Format Upload",

    'summary': "Format Upload",

    'description': """
        Master untuk format dokumen
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_menu','tw_config_files'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_format_upload_view.xml',
    ],
}

