# -*- coding: utf-8 -*-
{
    'name': "TW Custom WEB for TEDS 2.0",

    'summary': "Custom WEB for TEDS 2.0",

    'description': """
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    # * Don't depends tw_base, becase tw_base depends in this modules?
    'depends': ['base','web'],

    # always loaded
    'data': [
        'report/tw_report_component.xml',
        'report/tw_report_paperformat.xml',
        'report/tw_report_style_view.xml',
        'views/tw_web_view.xml',
    ],
}

