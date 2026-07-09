# -*- coding: utf-8 -*-
{
    'name': "TW BOOM Data Stock",

    'summary': "Bussines Operational Online Monitoring (BOOM) module for generate data Stock",

    'description': """
    This module provides tools to generate data BOOM with Main Category Stock .
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
    'depends': [
        'base',
        'tw_base',
        'tw_boom',
        ],

    # always loaded
    'data': [
        'data/scheduled_action.xml',
    ],
    "installable": True,
	"auto_install": False,
	"application": True,

}

