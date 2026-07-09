# -*- coding: utf-8 -*-
{
    'name': "TW Stock Adjustment",

    'summary': """
        Stock Adjustment module with approval workflow for inventory corrections.
    """,

    'description': """
        A module to manage stock adjustments with approval workflow.
        - Create adjustment records to correct stock quantities
        - Workflow: Draft → Confirm → Done
        - Integrates with stock.quant for quantity updates
        - Creates stock.move and stock.valuation.layer automatically
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'TW Stock / TW Stock',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'base_suspend_security',
        'stock',
        'tw_base',
        'tw_branch',
        'tw_product',
        'tw_selection',
        'tw_menu',
        'web_report',
        'tw_format_upload',
    ],

    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'wizard/tw_stock_adjustment_report_view.xml',

        'views/tw_stock_adjustment_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}
