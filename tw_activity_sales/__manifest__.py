# -*- coding: utf-8 -*-
{
    'name': "TW Activity Sales",

    'summary': "Module linked between Activity Plan BTL with Lead, DSO, and SPK",

    'description': """
        TW Activity Sales
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base'
        , 'tw_base'
        , 'tw_dealer_sale_order'
        , 'tw_lead_spk'
        , 'tw_activity_atl_btl'
        ],

    # always loaded
    'data': [
        'views/tw_activity_lead_view.xml',
        'views/tw_activity_dso_view.xml',
        'views/tw_activity_spk_view.xml',
    ],
    'external_dependencies' : {
    }

}

