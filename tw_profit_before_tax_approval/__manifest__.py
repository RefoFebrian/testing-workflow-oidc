# -*- coding: utf-8 -*-
{
    'name': "TW Profit Before Tax Approval",

    'summary': "Module to manage and approve profit before tax calculations.",

    'description': """
This module facilitates the approval process for profit before tax calculations. 
It ensures that all calculations are reviewed and approved according to the company's policies and procedures.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_profit_before_tax', 'tw_approval'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'views/tw_profit_before_tax_inherit_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

