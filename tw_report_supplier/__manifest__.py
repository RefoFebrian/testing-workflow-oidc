# -*- coding: utf-8 -*-
{
    'name': "TW Report Supplier",

    'summary': "TW Report Supplier",

    'description': """
TW Report Supplier
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
    'depends': ['base', 'tw_menu', 'web_report', 'tw_base'],

    # always loaded
    'data': [
        'report/tw_report_supplier_view.xml',

        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/tw_menu.xml',
    ],
}