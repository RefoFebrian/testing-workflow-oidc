# -*- coding: utf-8 -*-
{
    'name': "TW DB Config",

    'summary': """
        Module Config untuk DB connection""",

    'description': """
        Module dibuat untuk Config DB connection
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "http://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','bus','tw_menu'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/res_groups.xml',
        'views/tw_db_config_view.xml',
    	'security/ir.model.access.csv',
    ],
}