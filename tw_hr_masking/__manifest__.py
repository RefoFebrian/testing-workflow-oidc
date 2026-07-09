# -*- coding: utf-8 -*-
{
    'name': "TW HR Masking",

    'summary': "Masking sensitive data",

    'description': """
        Masking sensitive data
    """,

    'author': "Tunas Honda",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW HR / TW HR',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base'
                ,'hr'
                ,'tw_hr'
                ,'tw_mask_widget'
            ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tw_employee_view.xml',
    ],
    'demo': [],
    "installable": True,
	"auto_install": False,
	"application": True,
}

