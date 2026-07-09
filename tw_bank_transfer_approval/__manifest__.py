# -*- coding: utf-8 -*-
{
    'name': "TW Bank Transfer Approval",

    'summary': "TW Bank Transfer Approval",

    'description': """
TW Bank Transfer Approval
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
    'depends': ['base','tw_base','tw_approval','tw_bank_transfer'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups_button.xml',

        'views/tw_bank_transfer_view.xml',
    ]
}

