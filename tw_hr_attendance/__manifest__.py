# -*- coding: utf-8 -*-
{
    'name': "TW HR Attendance",

    'summary': "Training",

    'description': """
Long description of module's purpose
    """,

    'author': "PT. Tunas Dwipa Matra",
    'website': "https://www.yourcompany.com",
    'license': "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_api', 'tw_branch', 'tw_hr', 'tw_menu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tw_hr_attendance_view.xml',
        'views/tw_hr_attendance_request_view.xml',
        'views/tw_menu_view.xml',
        'views/res_company_inherit_view.xml',
        'report/tw_hr_attendance_report_view.xml',
    ],
}

