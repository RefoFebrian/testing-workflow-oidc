# -*- coding: utf-8 -*-
{
    'name': "TW Work Order",

    'summary': "Work Order for Vehicle Service",

    'description': """
Long description of module's purpose
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
        'sale',
        'sale_management',
        'stock',
        'hr',
        'product',
        'tw_branch',
        'tw_branch_setting',
        'tw_menu',
        'tw_web',
        'tw_stock',
        'tw_selection',
        'tw_sequence',
        'tw_account_setting',
        'tw_account_branch',
        'tw_pricelist_branch',
        'tw_payment',
        'tw_stock_qr_code',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        
        'wizard/tw_work_order_print_wizard_view.xml',
        'views/tw_work_order_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_stock_lot_view.xml',
        'views/tw_branch_setting_inherit_view.xml',

        'views/tw_workshop_category_view.xml',
        'views/tw_workshop_type_view.xml',

        'report/tw_service_wo_thermal_direct_print.xml',
        'report/tw_picking_list_wo_thermal_print.xml',
        'report/tw_wo_thermal_invoice_print_template.xml',
        'report/tw_wo_invoice_print.xml',
        'report/tw_wo_print.xml',

        'wizards/tw_serial_number_wizard_view.xml',
        'wizards/tw_unused_wizard_view.xml',
        
        'views/tw_menu.xml',

        'data/ir_config_parameter.xml',
        'data/tw_selection_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tw_work_order/static/src/scss/style.scss',
        ],
    },
}

