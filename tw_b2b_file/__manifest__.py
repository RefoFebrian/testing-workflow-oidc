# -*- coding: utf-8 -*-
{
    'name': "TW B2B File",

    'summary': "Managing B2B File",

    'description': """
A File Management Module application is a secure and efficient platform designed to facilitate seamless file sharing and collaboration between businesses.
It enables organizations to upload, store, organize, and share critical documents while maintaining strict access controls to ensure data confidentiality.
The module supports multiple file formats, version control, and real-time tracking of file activity, fostering transparency and accountability.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'account',
        'product', 
        'stock', 
        'stock_account', 
        'tw_account', 
        'tw_account_purchase', 
        'tw_account_setting', 
        'tw_purchase_order', 
        'tw_branch', 
        'tw_selection', 
        'tw_config_files',
        'tw_product', 
        'tw_stock', 
        'tw_stock_account', 
        'tw_stock_purchase', 
        'tw_b2b_file_stock', 
        'tw_account_discount', 
        'tw_faktur_pajak',
        ],

    # always loaded
    'data': [
        'data/tw_config_files_data.xml',
        'data/tw_cron_data.xml',
        'data/tw_separator_selection_data.xml',
        'data/tw_b2b_file_config_data.xml',
        
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_group_buttons.xml',
        
        'views/tw_b2b_file_config_views.xml',
        'views/tw_b2b_file_mft_config_views.xml',
        'views/tw_b2b_file_views.xml',
        'views/tw_b2b_file_content_views.xml',
        'views/tw_inherit_branch_view.xml',
        'views/tw_inherit_res_config_settings_view.xml',
        'views/tw_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}
