# -*- coding: utf-8 -*-
{
    'name': "TW Quality Checking",

    'summary': "The Quality Checking module enables efficient monitoring and control of product quality through customizable inspections and checkpoints across operations.",

    'description': """
The Quality Checking module in Odoo is designed to manage and monitor product quality throughout the operational process. It allows users to define quality checkpoints, create inspection criteria, and record results during receiving, production, or delivery stages. By integrating with inventory and manufacturing, the module helps ensure that only products meeting the required standards proceed further, reducing defects and improving customer satisfaction.

Key Features:
- Enhanced product bundling views
- Improved management of MRP processes
- Seamless integration with existing Odoo modules

This module is ideal for businesses looking to optimize their manufacturing processes and ensure accurate product bundling.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_stock','tw_menu','tw_selection'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_quality_checking_view.xml',
        'views/tw_cardboard_dimensions_view.xml',

        'reports/tw_quality_checking_actions.xml',
        'reports/template/tw_quality_checking_thermal_template.xml',
        'reports/template/tw_cartoon_pdf_template.xml',

        'views/tw_menu.xml',
    ],
}

