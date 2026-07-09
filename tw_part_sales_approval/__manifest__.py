# -*- coding: utf-8 -*-
{
    'name': "TW Part Sales Approval",

    'summary': "Part Sales Approval for Vehicle Service",

    'description': """
        TW Part Sales Approval
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Part Sales Approval',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_part_sales','tw_approval'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'views/tw_approval_part_sales_view.xml',
    ],
}

