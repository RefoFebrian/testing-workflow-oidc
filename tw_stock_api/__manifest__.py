# -*- coding: utf-8 -*-
{
    'name': "TW Stock API",

    'summary': "Integration Stock API",

    'description': """
        Integration Stock API
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'rest_api',
        'tw_api',
        'tw_stock',
        'tw_partner',
        ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/tw_partner_inherit_view.xml',
        'data/tw_cron_data.xml',
    ],
}

