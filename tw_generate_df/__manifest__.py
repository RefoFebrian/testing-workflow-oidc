# -*- coding: utf-8 -*-
{
    'name': "Tw Generate DF",

    'summary': "TW Generate DF",

    'description': """
TW Generate DF
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
    'depends': ['base','account','tw_base','tw_menu','tw_partner','tw_sale_drawdown'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/ir_configparameter_data.xml',
        'views/tw_generate_df_views.xml',
        'views/tw_res_partner_inherit.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}

