# -*- coding: utf-8 -*-
{
    "name": "TW Leads",
    "summary": "Module to record customers who have the potential to buy products",
    "description": """
        This module, named "Leads", is designed to manage customer prospects effectively. It provides a comprehensive system to record and track potential customers who have shown interest in purchasing products. The module integrates seamlessly with other essential modules such as TW Menu, TW Branch, Product, TW HR, TW HR Retailer, and TW Selection to ensure a smooth workflow and data consistency across the system.

        Key features of the Leads module include:
        - Recording detailed information about potential customers, including contact details, interests, and interaction history.
        - Categorizing leads based on various criteria to prioritize follow-ups and tailor marketing strategies.
        - Assigning leads to specific sales representatives or teams to ensure accountability and personalized communication.
        - Tracking the progress of each lead through different stages of the sales funnel, from initial contact to conversion.
        - Generating reports and analytics to evaluate the effectiveness of lead generation and management strategies.
        - Ensuring data security and access control through defined user roles and permissions.

        By using the Leads module, businesses can enhance their customer relationship management, improve sales efficiency, and ultimately increase conversion rates.
    """,
    "author": "TDM",
    "license": "LGPL-3",
    "website": "https://www.honda-ku.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "TW Sales / TW Sales",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "base", 
        "crm", 
        "tw_menu", 
        "tw_branch", 
        "tw_base",
        "tw_product", 
        "tw_partner",
        "tw_hr", 
        "tw_hr_retailer", 
        "tw_selection", 
        "tw_stock", 
        "tw_config_files",
        "tw_attachment"
    ],
    # always loaded
    "data": [
        'data/tw_lead_selection_data.xml',
        'data/tw_lead_stage_data.xml',
        'data/tw_sequence_data.xml',
        
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_lead_view.xml',
        'views/tw_selection_sales_channel_view.xml',
        'views/tw_selection_customer_grade_view.xml',
        'views/tw_selection_data_source_view.xml',
        'views/tw_selection_lead_web_source_view.xml',
        
        'views/tw_menu.xml',
        
    ]
}

    # NOTE:
    # these codes are copy and adjustment from tunashonda
    # but odoo officals already has crm.lead models that can be used
    # and utilised in the new teds 2.0
    
    # 'security/ir.model.access.csv',
    # 'security/ir_rule.xml',
    # 'views/tw_lead_view.xml',

