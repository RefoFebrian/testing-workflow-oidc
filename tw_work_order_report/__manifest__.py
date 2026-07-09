# -*- coding: utf-8 -*-
{
    'name': "TW Work Order Report",

    'summary': "TW Work Order Report",

    'description': """
        TW Work Order Report
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_menu',
        'tw_work_order',
        'tw_work_order_wip',
        'tw_work_order_api',
        'tw_work_order_voucher',
        'web_report',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'wizard/tw_work_order_print_wizard_inherit_view.xml',

        "report/tw_work_order_wip_report_view.xml",
        "report/tw_work_order_report_view.xml",
        "report/tw_wo_kwitansi_print.xml",

        "views/tw_work_order_inherit_view.xml",
        "views/tw_menu.xml",
    ],
}

