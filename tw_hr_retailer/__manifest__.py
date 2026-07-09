# -*- coding: utf-8 -*-
{
    'name': "TW HR for Retailer",

    'summary': "Human Resource addition for Retailer",

    'description': """
        Human Resource Modules addition for Retailer
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
    'depends': ['base','hr','tw_hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/res_groups.xml',
        # 'security/res_groups_job.xml',

        'views/tw_job_view.xml',
    ],
    'demo': [],
    "installable": True,
	"auto_install": False,
	"application": True,
}

