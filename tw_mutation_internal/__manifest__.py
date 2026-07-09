# -*- coding: utf-8 -*-
{
    'name': "TW Mutation Internal",

    'summary': "Mutation Internal",

    'description': """
        Mutation Internal Location
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','tw_base','tw_menu','tw_stock', 'tw_web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_mutation_internal_view.xml',

        'report/template/tw_mutation_internal_report_template.xml',
        'report/tw_mutation_internal_report_actions.xml',

        'views/tw_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}

