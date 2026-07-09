# -*- coding: utf-8 -*-
{
    'name': "TW RPA Sparepart Distribution",

    'summary': """
        RPA Sparepart Distribution
        """,

    'description': """
        Automates the transaction flow from Stock Distribution (SD) to Sales Order (SO) or Mutation Order (MO) until they are confirmed or completed.
        This module ensures seamless and efficient processing of spare part distribution by reducing manual intervention, minimizing errors, and accelerating transaction handling. 
        It enhances workflow automation, improves inventory management, and optimizes operational efficiency.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'TW Sales/ TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_selection',
        'tw_branch',
        'tw_sale',
        'tw_mutation',
        'tw_stock_distribution',
        'tw_sale_order_discount',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_sale_order_inherit_view.xml',
        'views/tw_mutation_order_inherit_view.xml',
        'views/tw_branch_setting_inherit_view.xml',
        'views/tw_partner_inherit_view.xml',
        'views/tw_rpa_sparepart_distribution_view.xml',
        'views/tw_schedule_shipment_views.xml',
        'views/tw_master_dealer_group_view.xml',

        'views/tw_menu.xml',
        'data/scheduled_actions.xml',
        'data/gc_user_parameter.xml',
    ],

    'application':True,
    'installable':True, 
}