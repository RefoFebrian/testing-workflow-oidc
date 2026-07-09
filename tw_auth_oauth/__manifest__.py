# -*- coding: utf-8 -*-
{
    'name': "TW Auth Oauth",

    'summary': """
        SSO Tunas Azure Login to TEDS 2.0""",

    'description': """
        SSO Tunas Azure Login to TEDS 2.0
    """,

    'author': "Tunas Honda",
    'website': "http://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_menu','auth_oauth','auth_totp','hr','tw_hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_auth_oauth_report_view.xml',
        
        'views/hr_employee_inherit_view.xml',
        'views/res_users_view.xml',
        'views/auth_oauth_view.xml',
        'views/tw_menu.xml',

        'data/ir_config_parameter.xml'
    ],
}
