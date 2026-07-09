# -*- coding: utf-8 -*-
{
    'name': "TW QTY Ideal Stock Report",

    'summary': "TW QTY Ideal Stock Report",

    'description': """
        TW QTY Ideal Stock Report
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
        'account',
        'tw_base',
        'tw_menu',
        'tw_branch',
        'tw_work_order',
        'web_report'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'wizard/tw_qty_stock_ideal_wizard_view.xml',

        'views/tw_menu.xml',
    ],
}

