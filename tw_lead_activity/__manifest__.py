# -*- coding: utf-8 -*-
{
    'name': "TW Lead Activity",

    'summary': "Tracking Leads or Prospects Follow ups Activity",

    'description': """
        This module enhances the management of Leads and Prospects by enabling comprehensive tracking of follow-up activities.
        
        Key Features:
        - Link Leads/Prospects with customizable Activity Plans.
        - Log, schedule, and monitor follow-up actions (calls, meetings, emails, etc.).
        - View activity history and upcoming actions directly from the Lead/Prospect form.
        - Automated reminders and status updates for pending activities.
        - User access control for managing and viewing activities.
        - Reports and dashboards for analyzing follow-up effectiveness.
        
        This helps sales teams ensure timely engagement, improve conversion rates, and maintain a clear record of all interactions with potential customers.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'tw_lead'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_lead_view_inherit.xml',
        'views/tw_lead_activity_result.xml',
        'wizard/tw_lead_activity_wizard_form.xml',
        
        'views/tw_menu.xml',
    ]
}

