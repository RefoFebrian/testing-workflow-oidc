# -*- coding: utf-8 -*-
{
    'name': "TW Progressive Tax Report",

    'summary': "TW Progressive Tax Report",

    'description': """
        TW Progressive Tax Report
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
        'tw_base',
        'tw_progressive_tax',
        'tw_dealer_sale_order',
        'tw_vehicle_document_report'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_progressive_tax_report_view.xml',

        'views/tw_menu.xml',
    ],
}

