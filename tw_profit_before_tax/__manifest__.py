# -*- coding: utf-8 -*-
{
    'name': "TW Profit Before Tax",

    'summary': "Module to calculate and display profit before tax for businesses.",

    'description': """
This module provides functionality to calculate and display the profit before tax 
for businesses. It includes tools for financial reporting and analysis, ensuring 
accurate and efficient tax-related computations.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_menu',
        'tw_incentive',
        'tw_config_files',
        'tw_format_upload',
        'tw_dealer_sale_order',
        'tw_dealer_sale_order_bbn',
        'tw_dealer_sale_order_program'
    ],

    # always loaded
    'data': [
        'data/data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'views/tw_approval_area_manager_view.xml',
        'views/tw_approval_general_manager_view.xml',
        # 'views/tw_dealer_sale_order_inherited_view.xml',
        'views/tw_period_profit_before_tax_view.xml',
        'views/tw_profit_before_tax_view.xml',
        # 'views/tw_target_margin_inherited_view.xml',

        'report/tw_progress_pbt_report_wizard.xml',
        'report/tw_summary_forecast_report_wizard.xml',
        'report/tw_target_net_margin_report_wizard.xml',

        'wizards/tw_download_profit_before_tax_wizard.xml',
        'wizards/tw_upload_period_profit_before_tax_wizard.xml',
        'wizards/tw_upload_profit_before_tax_wizard.xml',

        'views/tw_menu.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'external_dependencies' : {
        'python': ['pandas', 'openpyxl'],
    },
}

