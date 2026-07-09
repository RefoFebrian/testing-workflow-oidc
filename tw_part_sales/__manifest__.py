# -*- coding: utf-8 -*-
{
    'name': "TW Part Sales",

    'summary': "TW Part Sales",

    'description': """
        TW Part Sales
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Part Sales / TW Part Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'account_payment',
        'sale',
        'sale_management',
        'sales_team',
        'product',
        'tw_account_setting',
        'tw_branch_setting',
        'tw_menu',
        'tw_partner',
        'tw_print_counter'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_part_sales_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_menu_view.xml',

        'report/tw_part_sales_report_template.xml',
        'report/tw_part_sales_report_view.xml',
        'report/tw_part_sales_report.xml',
        'report/tw_part_sales_thermal_print.xml',
        'report/tw_part_sales_picking_thermal_print.xml',
    ],
}

