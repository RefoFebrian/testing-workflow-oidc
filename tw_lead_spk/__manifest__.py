# -*- coding: utf-8 -*-
{
    'name': "TW Lead SPK",

    'summary': "Extends Lead with SPK.",

    'description': """
This module is used to manage Extended process Lead from SPK.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_spk', 'tw_lead'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_lead_inherit_view.xml',
        'views/tw_dealer_spk_inherit_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}

