# -*- coding: utf-8 -*-
{
    'name': "TW Payment Klik Inherit Approval",

    'summary': "Adds an payment klik cancel on approval workflow.",

    'description': """
Long description of module's purpose
    This module adds an payment klik cancel on approval workflow.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_payment_klik','tw_payment','tw_approval','tw_payment_approval'],

    # always loaded
    'data': []
}

