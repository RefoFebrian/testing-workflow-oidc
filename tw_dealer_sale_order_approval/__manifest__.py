# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order Approval",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'tw_approval', 'tw_dealer_sale_order', 'tw_dealer_sale_order_bbn',
        'tw_dealer_sale_order_finco',
    ],

    # always loaded
    'data': [
        # 'data/approval_data.xml', #Dikomen karena data sudah di import
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_dealer_sale_order_approval_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}

