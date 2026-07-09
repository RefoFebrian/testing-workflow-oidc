# -*- coding: utf-8 -*-
{
    'name': 'TW DGI SPK',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'DGI API Integration for SPK',
    'description': """
        Integration module untuk sync data SPK dari DGI API
        - Sync SPK dari DGI
        - Sync Leasing data untuk pembayaran kredit
        - Auto create Sale Order
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'license': 'LGPL-3',
    
    'depends': [
        'base',
        'hr',
        'tw_base',
        'tw_spk',
        'tw_lead',
        'tw_lead_spk',
        'tw_branch',
        'tw_branch_setting',
        'tw_localization',
        'tw_selection',
        'tw_dealer_sale_order',
        'tw_dgi',
        'tw_dgi_lead',
        'tw_lead_dealer_sale_order',
    ],
    
    'data': [
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'data/tw_endpoint_dgi_spk_data.xml',
        'data/tw_endpoint_dgi_lsng_data.xml',
        'data/tw_mapping_dgi_lsng_data.xml',
        'data/tw_mapping_dgi_spk_data.xml',
        'views/tw_spk_view_inherit.xml',
        'views/tw_branch_setting_inherit_view.xml',
        'wizards/tw_dgi_spk_wizard_view.xml',
        'views/tw_lead_dgi_edit_view.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
