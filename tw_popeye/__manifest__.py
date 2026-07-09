# -*- coding: utf-8 -*-
{
    'name': "TW Popeye Integration",

    'summary': "Integrates Odoo with the Popeye Payment Gateway.",

    'description': """
        This module provides the necessary models and views to integrate Odoo's payment and bank transfer workflows with the external Popeye payment system.
        It allows sending transactions to Popeye and checking their status.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting/Accounting',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_menu',
        'account',
        'tw_account',
        'tw_payment', 
        'tw_bank_transfer', 
        'tw_api',
        'rest_api',
    ],

    # always loaded
    'data': [
        # Security
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        # Data
        'data/tw_api_configuration_data.xml',
        'data/ir_config_parameter.xml',
        'data/tw_account_payment_method_data.xml',
        
        # Views
        'views/res_config_settings_views.xml',
        'views/res_partner_bank_account_inherit_view.xml',
        'views/tw_api_config.xml',
        'views/tw_payment_views.xml',
        'views/tw_bank_transfer_views.xml',

        # Wizard
        'wizard/tw_popeye_cancel_wizard_view.xml',

        'report/tw_api_popeye_report_wizard_view.xml'
    ],
    
    'installable': True,
    'application': False,
}

