# -*- coding: utf-8 -*-
{
    'name': "TW NRFS Work Order",

    'summary': "NRFS Work Order",

    'description': """
        NRFS Work Order
    """,

    'license':'AGPL-3',
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
        'tw_nrfs',
        'tw_branch',
        'tw_partner',
        'tw_work_order'
        ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        
        'views/tw_nrfs_work_order_view.xml',
        'views/tw_work_order_view.xml',
    ],
    'installable': True,
    'application': True,
}

