# -*- coding: utf-8 -*-
{
    'name': "TW Sparepart Substitusi",

    'summary': """""",
    'description': """""",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': "LGPL-3",

    'depends': ['base','tw_menu','tw_product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_sparepart_substitusi.xml',
        'views/tw_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}