# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order (Full Features)",

    'summary': "Full Features Module for Dealer Sale Order.",

    'description': """
        This module is designed to streamline and manage retail sales processes, 
        providing tools for invoicing, reporting, and integration with other modules 
        to ensure smooth sales operations.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': True,

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'tw_dealer_sale_order',
        'tw_dealer_sale_order_approval',
        'tw_dealer_sale_order_bbn',
        'tw_dealer_sale_order_cancel',
        'tw_dealer_sale_order_cdb',
        'tw_dealer_sale_order_commission',
        'tw_dealer_sale_order_direct_gift',
        'tw_dealer_sale_order_extra_reward',
        'tw_dealer_sale_order_faktur_pajak',
        'tw_dealer_sale_order_finco',
        'tw_dealer_sale_order_hutang_lain',
        'tw_dealer_sale_order_margin',
        'tw_dealer_sale_order_program',
        'tw_dealer_sale_order_voucher',
        ],

    # always loaded
    'data': [],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

