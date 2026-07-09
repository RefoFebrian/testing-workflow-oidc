# -*- coding: utf-8 -*-
{
    'name': "TW Vehicle",

    'summary': "Vehicle",

    'description': """
        Vehicle of Expedisi
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
    'depends': ['base','base_suspend_security','tw_partner','tw_menu'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_vehicle_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}

