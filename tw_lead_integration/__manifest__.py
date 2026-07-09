# -*- coding: utf-8 -*-
{
    'name': "TW Lead with Integration Source",

    'summary': "Lead with Integration Source",

    'description': """
    Lead with Integration Source
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_lead',
        'tw_selection',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/lead_source_data.xml',
        'views/tw_lead_integration_view.xml',
        'views/tw_selection_lead_source_data_view.xml',
        'views/tw_menu.xml',
    ],  
}

