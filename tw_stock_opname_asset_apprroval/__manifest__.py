# -*- coding: utf-8 -*-
{
    'name': "TW Stock Opname Asset Approval",

    'summary': "TW Stock Opname Asset Approval",

    'description': """
        TW Stock Opname Asset Approval
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
        'tw_stock_opname_asset',
        'tw_approval',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_stock_opname_asset_approval_view.xml',
    ],
}

