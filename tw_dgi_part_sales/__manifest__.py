# -*- coding: utf-8 -*-
{
    'name': "TW DGI Part Sales",

    'summary': "TW DGI Part Sales",

    'description': """
        TW DGI Part Sales
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_api',
        'tw_dgi',
        'tw_part_sales'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'data/tw_endpoint_dgi_part_sales_data.xml',
        'data/tw_mapping_dgi_part_sales_data.xml',

        'views/tw_part_sales_inherit_view.xml',

        'wizards/tw_dgi_part_sales_wizard_view.xml',
        'wizards/tw_dgi_info_wizard_inherit_view.xml',
    ],
}

