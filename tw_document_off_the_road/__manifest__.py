# -*- coding: utf-8 -*-
{
    'name': "TW Document Off The Road",

    'summary': "TW Document Off The Road",

    'description': """
        TW Document Off The Road
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
    'depends': [
        'base',
        'account',
        'stock',
        'tw_base',
        'tw_menu',
        'tw_vehicle_document',
        'tw_vehicle_document_receipt',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_submission_of_the_road_view.xml',
        'views/tw_process_off_the_road_view.xml',
        'views/tw_account_setting_inherit_view.xml',

        'views/tw_stock_lot_inherit_view.xml',
        
        'views/tw_menu.xml',
    ],
}

