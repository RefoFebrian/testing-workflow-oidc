# -*- coding: utf-8 -*-
{
    'name': "TW Stock Opname Api",

    'summary': """
        A module that ensures inventory accuracy by verifying physical stock against system data and noting differences.
    """,

    'description': """
        The Stock Opname Module is used to record and verify the accuracy of physical stock against system data. 
        This process includes recording stock discrepancies, adjusting data, and reporting opname results. 
        The module is designed to ensure inventory data accuracy and support decision-making in stock management.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Web / TW Web',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','rest_api', 'tw_api','tw_firebase','tw_stock_opname'],
    'data': [
        'data/scheduled_action.xml',
        'data/tw_firebase_content_template_data.xml',
        'data/tw_firebase_notification_category.xml',
    ],
}