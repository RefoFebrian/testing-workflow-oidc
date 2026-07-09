# -*- coding: utf-8 -*-
{
    'name': "TW BOOM",

    'summary': "Bussines Operational Online Monitoring (BOOM) module",

    'description': """
        This module provides tools to manage and monitoring 
        transaction for every salesman in every branch. 
        It enables users to track sales activities, 
        monitor sales performance, and generate reports for better 
        decision-making and operational efficiency.
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
        'tw_area',
        'tw_menu',
        ],

    # always loaded
    'data': [
        # 'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        "data/tw_boom_main_category_data.xml",
        "data/tw_boom_sub_category_data.xml",
        "data/tw_boom_category_data.xml",
        "data/tw_boom_master_quotes_data.xml",
        "data/scheduled_actions.xml",

        "views/tw_boom_main_category_view.xml",
        "views/tw_boom_sub_category_view.xml",
        "views/tw_boom_category_view.xml",
        "views/tw_boom_master_escalation_view.xml",
        "views/tw_boom_task_view.xml",
        "views/tw_boom_task_delegated_view.xml",
        "views/tw_boom_delegation_task_view.xml",
        "views/tw_boom_master_quotes_view.xml",
        "views/tw_boom_task_history_view.xml",

        "report/tw_boom_task_report_view.xml",
        "report/tw_boom_task_delegate_report_view.xml",

        'views/tw_menu.xml',
        
    ],
    "installable": True,
	"auto_install": False,
	"application": True,

}

