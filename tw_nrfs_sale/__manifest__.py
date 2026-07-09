# -*- coding: utf-8 -*-
{
    'name': "TW NRFS Sale",

    'summary': "NRFS Sale",

    'description': """
        NRFS Sale
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_nrfs_sparepart',
        'tw_sale'
        ],

    # always loaded
    'data': [
        'views/tw_nrfs_sale_order_view.xml',
        'views/tw_sale_order_inherit_view.xml'
    ],
    'installable': True,
    'application': True,
}

