# -*- coding: utf-8 -*-
{
    'name': "TW Stock Indbound",

    'summary': "The Expedition Module facilitates the management of expedition data and monitoring of ongoing shipments to support operational efficiency.",

    'description': """
The Expedition Module facilitates the management of expedition data and monitoring of ongoing shipments to support operational efficiency.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Web / TW Web',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base'
                ,'stock'
                ,'tw_pricelist'
                ,'tw_selection'
                ,'tw_base'
                ,'tw_menu'
                ,'tw_partner'
                ,'tw_branch_setting'
                ,'tw_stock'
                ,'tw_vehicle'
                ],

    # always loaded
    'data': [
        'data/data_contact_tags.xml',
        
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_stock_inbound_view.xml',
        'views/tw_expedition_master_view.xml',
        'views/tw_driver_master_view.xml',
        'views/tw_stock_picking_batch_inherit.xml',
        'views/tw_stock_picking_inherit_view.xml',
        'views/tw_product_pricelist_item_inherit_view.xml',
        'views/tw_menu.xml',
        'views/tw_branch_setting_inherit_view.xml',
    ],

}
