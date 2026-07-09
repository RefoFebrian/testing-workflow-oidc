# -*- coding: utf-8 -*-
{
    'name': "TW SPK",

    'summary': "SPK management for Honda dealers.",

    'description': """
This module is used to manage SPK at Honda dealers.
Main features include recording, tracking, and managing SPK data integrated with other related modules.
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
    'depends': ['base', 'tw_base', 'tw_selection', 'tw_dealer_sale_order'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'report/tw_dealer_spk_report_view.xml',
        'views/tw_dealer_spk_view.xml',
        'views/tw_dealer_sale_order_inherit_view.xml',
        'views/tw_menu.xml',
        
        'wizards/tw_dealer_spk_cancel_reason_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

