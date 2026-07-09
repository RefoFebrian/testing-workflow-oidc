# -*- coding: utf-8 -*-
{
    'name': "TW Auth Totp",

    'summary': "MFA for Tunas Honda",

    'description': """
MFA for Tunas Honda
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','web','tw_base','auth_oauth','auth_totp'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/tw_auth_totp_view.xml',
        'template/register_qrcode.xml'
    ],
}

