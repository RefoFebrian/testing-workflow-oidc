# -*- coding: utf-8 -*-
{
    'name': "TW Faktur Pajak Gabungan Coretax",

    'summary': "TW Faktur Pajak Gabungan Coretax",

    'description': """
    TW Faktur Pajak Gabungan Coretax
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base','tw_faktur_pajak_core_tax','tw_faktur_pajak_gabungan'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ]
}

