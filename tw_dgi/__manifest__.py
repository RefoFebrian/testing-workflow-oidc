# -*- coding: utf-8 -*-
{
    'name': "Dealer Group Integration",
    'summary': "Integration with Dealer Group Systems",
    'description': """
        Tunas Dealer Group Integration
        =============================
        
        This module provides integration between Odoo and external Dealer Group systems.
        It includes API configurations, endpoint management, and response mapping
        for seamless data synchronization.
        
        Key Features:
        - API Configuration Management
        - Endpoint Configuration
        - Response Mapping
        - Secure API Authentication
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'API Integration',
    'version': '18.0.0.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'hr',
        'tw_api',
        'tw_branch',
        'tw_branch_setting',
        'tw_selection',
        'rest_api',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'wizards/response_mapping_import_wizard_view.xml',
        'wizards/tw_endpoint_config_wizard_view.xml',
        'wizards/tw_dgi_info_wizard_view.xml',
        'views/tw_mapping_response_view.xml',
        'views/tw_endpoint_configuration_view.xml',
        'views/tw_endpoint_output_template_form.xml',
        'views/tw_api_configuration_inherit_view.xml',
        'views/tw_branch_setting_inherit_view.xml',
        'views/tw_hr_employee_inherit_view.xml',

        'data/tw_api_configuration_type_data.xml',
        'data/tw_api_configuration_dgi_data.xml',
        'data/tw_selection_division_dgi_data.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
