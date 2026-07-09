# -*- coding: utf-8 -*-
{
    'name': "TW MFT File SSU",

    'summary': "MFT File SSU",

    'description': """
        Generate data SSU for send to AHM
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_stock',
        'tw_config_files',
        'tw_selection',
        'tw_branch',
        'tw_base',
        ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/tw_cron_data.xml',
        'views/tw_mft_file_ssu_view.xml',
        'views/tw_inherit_stock_lot_view.xml',
        'report/b2b_file_receive_report.xml',
    ],
    'installable': True,
    'application': True,
}
