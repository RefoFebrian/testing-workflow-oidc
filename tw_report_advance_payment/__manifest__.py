# -*- coding: utf-8 -*-
{
    'name': "TW Report Advance Payment",

    'summary': "TW Report Advance Payment",

    'description': """
    Report Advance Payment & Settlement Advance Payment
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
    'depends': ['base', 'web_report', 'tw_menu', 'tw_advance_payment', 'tw_settlement'],

    # always loaded
    'data': [
        'report/tw_report_advance_payment_view.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_menu.xml',
    ],
}