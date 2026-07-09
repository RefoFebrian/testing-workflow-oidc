# -*- coding: utf-8 -*-
{
    'name': "TW Part Hotline Approval",

    'summary': "TW Part Hotline Approval",

    'description': """
TW Part Hotline Approval
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'tw_base',
        'tw_part_hotline',
        'tw_approval',
        'tw_purchase_order'
    ],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_part_hotline_inherit_view.xml',
        'views/tw_purchase_order_inherit.xml',
    ],
}

