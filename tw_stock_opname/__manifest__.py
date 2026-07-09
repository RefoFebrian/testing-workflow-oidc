# -*- coding: utf-8 -*-
{
    'name': "TW Stock Opname",

    'summary': """
        A module that ensures inventory accuracy by verifying physical stock against system data and noting differences.
    """,

    'description': """
        The Stock Opname Module is used to record and verify the accuracy of physical stock against system data. 
        This process includes recording stock discrepancies, adjusting data, and reporting opname results. 
        The module is designed to ensure inventory data accuracy and support decision-making in stock management.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Web / TW Web',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base'
                ,'base_suspend_security'
                ,'rest_api'
                ,'tw_base'
                ,'tw_product'
                ,'tw_stock'
                ,'tw_selection'
                ,'tw_menu'
                ,'tw_branch'
                ,'tw_config_files'
                ,'tw_hr'
                ,'web_report'
                , 'tw_web'
            ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/tw_menu.xml',
        'views/tw_stock_opname_view.xml',
        'views/tw_stock_opname_retail_view.xml',
        'views/tw_stock_opname_partial_view.xml',
        'views/tw_stock_opname_upload_view.xml',
        'views/tw_stock_opname_photo_view.xml',
        'views/tw_stock_opname_detail_view.xml',
        'views/tw_stock_opname_pic_view.xml',

        'report/tw_reports.xml',
        'report/tw_stock_opname_report_view.xml',
        'report/tw_stock_opname_unit_validation_report_template.xml',
        'report/tw_berita_acara_so_sparepart.xml',
        'report/tw_berita_acara_so_unit.xml',
        'report/tw_stock_opname_baso_view.xml',

        'data/tw_stock_opname_condition_data.xml',
    ],
    # TODO : Lakukan Penyesuaian JS berikut jika masih ingin memakai fitur maps pada stock opname
    # 'assets': {
    #     'web.assets_backend': [
    #         'tw_stock_opname/static/src/js/dynamic_map.js',
    #     ],
    # },
}
