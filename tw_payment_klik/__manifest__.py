# -*- coding: utf-8 -*-
{
    'name': 'TW Report Payment Klik',
    'version': '0.1',
    'category': 'TDM',
    'summary': 'Payment Klik Reporting',
    'description': """
        TW Report Payment Klik
        ===========================
        
        This module handles payment klik reporting functionality.
    """,
    'author': 'Tunas Group',
    'website': 'https://www.tunasgroup.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_suspend_security',
        'web_report',
        'tw_base',
        'tw_account',
        'tw_selection',
        'tw_payment',
        'tw_advance_payment',
        'tw_bank_transfer',
        'tw_settlement',
        'tw_branch_setting',
    ],
    'data': [
        'data/config_params_bank_code_data.xml',
        'data/ir_cron.xml',

        'security/res_groups.xml',
        'security/res_group_button.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',

        'views/tw_account_payment_view.xml',
        'views/tw_advance_payment_view.xml',
        'views/tw_bank_transfer_view.xml',
        'views/tw_settlement_view.xml',
        'views/tw_payment_klik_report_wizard.xml',
        'views/tw_payment_klik_monitoring_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
