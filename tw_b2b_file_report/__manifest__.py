# -*- coding: utf-8 -*-
{
    'name': "TW B2B File Report",

    'summary': "B2B File Report",

    'description': """
        B2B File Report
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
        'tw_base',
        'tw_menu',
        'web_report',
        'tw_b2b_file',
        'tw_b2b_file_stock',
        'tw_stock',
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_b2b_file_psl_report_view.xml',
        'views/tw_b2b_file_ps_report_view.xml',
        'views/tw_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}

