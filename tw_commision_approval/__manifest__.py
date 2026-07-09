# -*- coding: utf-8 -*-
{
    'name': "TW Commission Approval",

    'summary': "Approval Hutang Komisi",

    'description': """
Approval Hutang Komisi
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
    'depends': ['base','tw_base','tw_approval','tw_commission'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_commission_approval_view.xml',
    ]
}

