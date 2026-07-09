# -*- coding: utf-8 -*-
{
    'name': "TW Firebase",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_menu', 'tw_api', 'tw_lead_activity'],

    # always loaded
    'data': [
        "data/scheduled_actions.xml",
        "data/tw_firebase_content_template_data.xml",
        "data/tw_firebase_notification_category.xml",
        "data/tw_firebase_selection_type_data.xml",

        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "security/res_groups.xml",
        "security/res_groups_button.xml",
        "security/tw_firebase_api_configuration_group.xml",
        "security/tw_firebase_content_template_group.xml",
        "security/tw_firebase_message_group.xml",
        "security/tw_firebase_notification_category_group.xml",
        "security/tw_firebase_notification_group.xml",
        "security/tw_firebase_user_group.xml",
        
        "views/tw_firebase_api_configuration_view.xml",
        "views/tw_firebase_content_template_view.xml",
        "views/tw_firebase_message_view.xml",
        "views/tw_firebase_notification_category_view.xml",
        "views/tw_firebase_notification_view.xml",
        "views/tw_firebase_user_view.xml",

        "views/tw_menu.xml",
    ],

    "external_dependencies" : {
        "python" : ["pyfcm"],
    }
}

