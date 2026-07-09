# -*- coding: utf-8 -*-
{
    'name': "TW Pilot Project",

    'summary': "Pilot Project",

    'description': """
        This Module helps organizations test new solutions before full implementation, minimize risks and ensure project success.
    """,

    'author': "Tunas Honda",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_branch'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_pilot_project.xml',

        'data/tw_pilot_project_output_type_data.xml',
    ],
    
    # only loaded in demonstration mode
    'demo': [],
}