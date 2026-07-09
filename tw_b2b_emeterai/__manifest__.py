{
    'name': "TW B2B E-Meterai",

    'summary': "Module to integrate and manage electronic stamp duty (e-Meterai) for B2B documents.",

    'description': """
This module provides functionality to apply, manage, and validate electronic stamp duty (e-Meterai)
on business-to-business documents such as invoices, contracts, and agreements.
It supports integration with e-Meterai services, ensures compliance with government regulations,
and helps businesses streamline their digital documentation processes.
Ideal for companies that need secure, legally recognized, and efficient handling of digital stamp duty.
""",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'tw_base',
        'tw_menu',
        'tw_selection',
        'tw_branch',
        'tw_api',
        'tw_config_files',
        'web_report',
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/tw_api_configuration_type_data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'report/tw_b2b_emeterai_report_view.xml',

        'views/tw_api_configuration_inherit_view.xml',
        'views/tw_b2b_emeterai_master_coordinate_view.xml',
        'views/tw_b2b_emeterai_master_quota_view.xml',
        'views/tw_b2b_emeterai_view.xml',
        'views/tw_menu_view.xml',
    ],
}