# -*- coding: utf-8 -*-
{
    'name': "TW HR Report",

    'summary': "TW HR Report",

    'description': """
        TW HR Report
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
    'depends': ['base','tw_base','tw_hr','tw_menu','tw_mekanik_mitra'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_employee_report_view.xml',
        'report/tw_employee_historical_report_view.xml',

        'views/tw_menu.xml',
    ],
}

