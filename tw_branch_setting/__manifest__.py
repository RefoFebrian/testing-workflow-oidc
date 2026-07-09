# -*- coding: utf-8 -*-
{
    'name': "TW Branch Setting",

    'summary': "Branch setting",
 
    'description': """
Branch setting
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
    'depends': ['base',
                'hr',
                'tw_selection',
                'tw_branch',
                'tw_base',
            ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'data/tw_branch_setting_config.xml',

        'views/tw_branch_setting_view.xml',
        'views/tw_branch_inherit_view.xml',
    ],
}

