{
    'name': "TW Ranking Sparepart Report",

    'summary': "Comprehensive ranking sparepart reporting module with advanced filtering and Excel export, designed to support effective stock control across branches and teams.",

    'description': """
        This module provides detailed ranking sparepart reporting capabilities. 
        It supports filtering by branch, product, category, date, and other criteria. 
        Reports can be exported to Excel format. 
        It is highly useful for warehouse teams, auditors, management, and operational staff for effective stock control and decision-making.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'product',
        'tw_product',
        'tw_branch',
        'tw_work_order',
        'tw_part_sales',
        'web_report',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_ranking_sparepart_report_view.xml',
        'views/tw_menu_view.xml',
    ],
}

