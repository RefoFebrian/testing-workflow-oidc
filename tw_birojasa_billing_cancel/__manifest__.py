{
    'name': 'TW Birojasa Billing Cancellation',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Handle cancellation of Birojasa Billing',
    'description': """
        Birojasa Billing Cancellation
        ==============================
        
        This module provides functionality to cancel Birojasa Billing
        with proper state management and approval workflow.
        
        Features:
        - Cancellation request for Birojasa Billing
        - Multi-level approval workflow
        - Integration with accounting journal entries
        - Security and access control
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'account',
        'tw_approval',
        'tw_account_setting',
        'tw_birojasa_billing_process',
        'tw_vehicle_document_cancel',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        'views/tw_birojasa_billing_cancel_views.xml',
        'views/tw_account_setting_views.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
