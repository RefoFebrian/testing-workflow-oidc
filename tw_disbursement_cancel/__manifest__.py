# -*- coding: utf-8 -*-
{
    'name': "TW Disbursement Cancel",

    'summary': "Allows users to cancel disbursement with proper validations.",

    'description': """
        This module provides functionality to cancel disbursement in Odoo. 
        It ensures that proper validations are in place before a disbursement can be canceled, 
        helping to maintain data integrity and avoid accidental cancellations. 
        The module integrates seamlessly with existing Odoo modules such as 'account', 'tw_base', 
        'tw_selection', and 'tw_account_period', ensuring compatibility and extended functionality.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'tw_disbursement',
        'tw_cancellation',
        'tw_account_setting',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_disbursement_cancel_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',
        
        'data/tw_cancellation_handler_data.xml'
    ],

}

