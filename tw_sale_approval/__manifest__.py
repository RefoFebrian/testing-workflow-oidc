# -*- coding: utf-8 -*-
{
    'name': "TW Sale Approval",

    'summary': "Connecting Sales to Approval Module",

    'description': """
        Connecting Sales to Approval Module
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','base_suspend_security','tw_sale','tw_approval'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',

        'views/tw_sale_approval_view.xml',
    ],
    'installable': True,
    'application': True,
}

