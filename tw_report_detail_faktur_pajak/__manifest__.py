# -*- coding: utf-8 -*-
{
    'name': "TW Report Detail Faktur Pajak",

    'summary': "TW Report Detail Faktur Pajak",

    'description': """
TW Report Detail Faktur Pajak
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_menu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_detail_faktur_pajak_masukan_views.xml',
    ],
    'application': False,
    'installable': True,
}

