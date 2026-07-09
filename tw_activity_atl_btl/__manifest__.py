# -*- coding: utf-8 -*-
{
    'name': "TW Activity Plan ATL BTL",

    'summary': "Manage and streamline activity planning and execution for ATL and BTL.",

    'description': """
        This module provides tools to manage Sales Activity Plans, ATL & BTL marketing activities.
        It enables users to define activity types,
        manage approvals, track results, and generate reports for better decision-making and
        operational efficiency.
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
        'product',
        'tw_base',
        'tw_menu',
        'tw_hr',
        'tw_selection',
        'tw_localization',
        'tw_product',
        'tw_ring',
        'tw_stock',
        'tw_stock_location_btl',
        'tw_map_widget'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'data/ir_config_parameter_data.xml',
        'data/tw_jenis_pengajuan_data.xml',
        # 'data/tw_master_activity_type_data.xml',
        'data/tw_titik_keramaian_category_data.xml',
        'data/tw_profile_consumen_data.xml',
        'data/tw_competitor_data.xml',
        'data/tw_schedule_done_activity.xml',
        'data/tw_sumber_pembayaran_btl_data.xml',

        'wizard/tw_payment_activity_wizard_view.xml',

        'views/tw_titik_keramaian_view.xml',
        'views/tw_mapping_titik_keramaian_view.xml',
        'views/tw_master_activity_type_view.xml',
        'views/tw_activity_atl_btl_detail_view.xml',
        'views/tw_activity_atl_btl_view.xml',
        'views/tw_outstanding_atl_btl_view.xml',
        'views/tw_lpj_atl_btl_view.xml',
        'views/tw_activity_atl_btl_result_view.xml',
        'views/tw_selection_sumber_pembayaran_btl_view.xml',
        'views/tw_selection_profile_consumen_view.xml',
        'views/tw_selection_dealer_competitor_view.xml',
        'views/tw_selection_titik_keramaian_category_view.xml',
        'reports/tw_activity_atl_btl_report_wizard_view.xml',
        'reports/tw_activity_atl_btl_print_template.xml',
        'reports/tw_activity_atl_btl_print_view.xml',
        'reports/tw_activity_atl_btl_insurance_report_wizard_view.xml',

        'views/tw_menu_view.xml',

    ],
    # 'external_dependencies' : {
    #     'python': ['haversine'],
    # },

}

