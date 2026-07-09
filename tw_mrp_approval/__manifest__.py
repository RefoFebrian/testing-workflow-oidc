# -*- coding: utf-8 -*-
{
    'name': "TW Mrp Approval",

    'summary': "TW Mrp Approval",

    'description': """
TW Mrp Approval
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_mrp','mrp','tw_mrp_bundling','tw_approval'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_mrp_production_view_inherit.xml',
    ],
}

