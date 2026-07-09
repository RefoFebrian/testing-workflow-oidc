# -*- coding: utf-8 -*-
{
    'name': "TW Report Tracking Quantity",

    'summary': "TW Report Tracking Quantity",

    'description': """
TW Report Tracking Quantity
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
    'depends': ['base', 'tw_menu', 'web_report'],

    # always loaded
    'data': [
        'report/tw_report_tracking_quantity_view.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_menu.xml',
    ],
}