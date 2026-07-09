# -*- coding: utf-8 -*-
{
    'name': "TW Checklist Tool",
    'version': '1.0.0',
    'summary': "Checklist Tool",

    'description': """
Long description of module's purpose
    """,

    'author': "Tunas Honda",
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',

    'category': 'Uncategorized',

    'depends': ['base', 'tw_product', 'tw_partner_cdb', 'tw_menu', 'tw_selection', 'tw_sequence'],

    'data': [
        'security/res_groups.xml',
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'data/tw_master_tools_location_data.xml',
        'data/tw_master_category_tools_data.xml',

        'report/tw_checklist_tool_print_template.xml',

        'views/tw_checklist_tools_view.xml',
        'views/tw_master_tools_view.xml',
        'views/tw_master_category_tools_selection_view.xml',
        'views/tw_master_tools_location_selection_view.xml',
        'views/tw_upload_message_wizard_view.xml',
        'views/tw_menu.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

