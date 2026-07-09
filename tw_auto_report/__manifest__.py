# -*- coding: utf-8 -*-
{
    'name': "TW Auto Report",

    'summary': "Automates the generation and management of reports for streamlined business operations.",

    'description': """
        This module is designed to automate the creation, scheduling, and management of business reports. 
        It provides tools to define report templates, set up automated report generation based on specific triggers or schedules, 
        and manage access permissions for different user groups. By streamlining the reporting process, 
        this module helps businesses save time, reduce errors, and ensure consistent reporting practices.
    """,

    'author': "Tunas Honda",
    'website': "http://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license':'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_menu','tw_base','tw_config_files'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'views/tw_report_automation_views.xml',

        'data/data_config_files.xml',
    ],
    'installable': True,
    'application': False,
}

