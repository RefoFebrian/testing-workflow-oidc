# -*- coding: utf-8 -*-
{
    'name': "TW BOOM Escalation",

    'summary': "Bussines Operational Online Monitoring (BOOM) module for escalation",

    'description': """
        This module provides tools to manage escalation 
        transaction for every salesman in every branch. 

        This module extends the functionality of the BOOM module 
        combine with WhatsApp API module to notify the escalation 
        transaction to the assigned employee.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_boom',
        'tw_whatsapp_api',
        ],

    # always loaded
    'data': [
        "data/tw_whatsapp_boom_type.xml",
        "data/tw_whatsapp_boom_template.xml",
        "data/scheduled_actions.xml",
        
        # 'security/ir_rule.xml',
        # 'security/ir.model.access.csv',
        # 'security/res_groups.xml',
        # 'security/res_groups_button.xml',

        "views/tw_boom_task_escalation_inherit_view.xml",
    ],
    "installable": True,
	"auto_install": False,
	"application": True,

}

