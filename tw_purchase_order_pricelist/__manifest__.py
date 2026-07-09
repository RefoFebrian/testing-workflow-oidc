# -*- coding: utf-8 -*-
{
    'name': "TW Pricelist Purchase Order",

    'summary': "Module to manage purchase orders with specific pricelists",

    'description': """
    This module extends the functionality of purchase orders in Odoo by integrating specific pricelists. 
    It allows users to apply predefined pricelists to purchase orders, ensuring consistent pricing and 
    streamlined procurement processes. Key features include:
    - Integration with existing purchase order workflows
    - Ability to apply specific pricelists to purchase orders
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Purchases',
    'version': '0.1',
    'license':'AGPL-3',

    'depends': ['base', 'tw_base','purchase', 'tw_purchase_order', 'tw_pricelist_branch'],

    'data': [
        'views/res_config_settings_view.xml',
        'views/tw_purchase_order_view.xml',
    ],
}

