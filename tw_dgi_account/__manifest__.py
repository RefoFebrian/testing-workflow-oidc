# -*- coding: utf-8 -*-
{
    'name': "DGI Account Integration (TEDS 2.0)",
    'summary': "Integration for DGI Invoice (INV1 & INV2) bypassing individual MD modules",
    'description': """
        Tunas Dealer Group Integration - Account
        ========================================
        
        This module provides integration between Odoo and external Dealer Group systems
        for Invoicing B2B (INV1 for Unit Sales and INV2 for Service/Spareparts).
        It utilizes the central configuration of tw_dgi to handle authentication and API endpoints.
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'API Integration',
    'version': '18.0.0.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'tw_dgi',
        'tw_dealer_sale_order', # For tw.dealer.sale.order
        'tw_work_order', # For tw.work.order
    ],
    'data': [
        'security/res_groups.xml',
        'data/ir_cron_data.xml',
        'views/tw_dealer_sale_order_inherit_view.xml',
        'views/tw_work_order_inherit_view.xml',
        'views/tw_endpoint_configuration_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
