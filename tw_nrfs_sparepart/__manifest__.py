# -*- coding: utf-8 -*-
{
    'name': "TW NRFS Sparepart",

    'summary': "NRFS Sparepart",

    'description': """
        NRFS Sparepart
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
        'tw_base',
        'base_suspend_security',
        'tw_nrfs',
        'tw_nrfs_stock',
        'tw_stock',
        'tw_partner'
        ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_nrfs_sparepart_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}

