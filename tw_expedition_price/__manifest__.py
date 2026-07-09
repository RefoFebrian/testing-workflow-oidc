# -*- coding: utf-8 -*-
{
    'name': "TW Expedition Price",

    'summary': "Pricelist Expedition",

    'description': """
        Pricelist Expedition for Every Single Branch
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
    'depends': ['base','base_suspend_security','tw_branch','tw_partner'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'views/tw_expedition_price_view.xml',
        'views/tw_menu.xml'
    ],
    'installable': True,
    'application': True,
}

