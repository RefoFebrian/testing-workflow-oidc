# -*- coding: utf-8 -*-
{
    'name': 'TW DGI Lead',
    'version': '1.0.0',
    'category': 'Sales/CRM',
    'summary': 'DGI API Integration for Lead/Prospect',
    'description': """
        Integration module untuk sync data Prospect/Lead dari DGI API
        - Sync Prospect dari DGI
        - Auto mapping ke tw.lead
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'license': 'LGPL-3',
    
    'depends': [
        'base',
        'hr',
        'tw_base',
        'tw_lead',
        'tw_lead_integration',
        'tw_branch',
        'tw_branch_setting',
        'tw_localization',
        'tw_selection',
        'tw_dgi',
        'tw_activity_atl_btl',
    ],
    
    'data': [
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'data/tw_endpoint_dgi_prospect_data.xml',
        'data/tw_mapping_dgi_prospect_data.xml',
        'views/tw_lead_view_inherit.xml',
        'views/tw_activity_atl_btl_view_inherit.xml',
        'wizards/tw_dgi_lead_wizard_view.xml',
        'wizards/tw_dgi_info_wizard_inherit_view.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
