# -*- coding: utf-8 -*-
{
    'name': "TW Report Faktur Pajak",

    'summary': "TW Report Faktur Pajak",

    'description': """
TW Report Faktur Pajak
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_menu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'wizard/tw_report_faktur_pajak_wizard.xml',
    ],
    'installable': True,
    'application': False,
}

