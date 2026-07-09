{
    'name': "TW SP Digital",

    'summary': "Module to generate and manage employee warning letters for disciplinary actions.",

    'description': """
This module provides functionality to create, manage, and track employee warning letters 
related to disciplinary actions. It supports the generation of formal warning documents, 
stores records for HR reference, and helps ensure compliance with company policies. 
Ideal for HR departments to maintain transparency and documentation throughout 
the disciplinary process.
""",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_menu',
        'tw_selection',
        'tw_hr',
        'tw_config_files',
        'tw_approval',
        # 'tw_whatsapp_api',
        'tw_incentive',
        # 'tw_format_upload',
        # 'tw_dealer_sale_order'
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',
        # 'data/tw_sp_digital_template_email.xml',
        'data/tw_sp_digital_send_email.xml',
        'data/tw_sp_digital_template_email_approval.xml',
        'data/tw_sp_digital_send_email_approval.xml',
        'data/tw_sp_digital_employee_ep.xml',
        'data/tw_sp_digital_config_param_data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
		'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'report/tw_report_sp_digital_view.xml',
        'report/tw_sp_digital_pdf_view.xml',

        'views/hr_employee_inherit_view.xml',
        'views/tw_sp_digital_view.xml',
        'views/tw_sp_digital_target_view.xml',
        'views/tw_upload_sp_digital_view.xml',
        'views/tw_menu_view.xml',
    ],
}