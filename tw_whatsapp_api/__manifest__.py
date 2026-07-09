# -*- coding: utf-8 -*-
{
    'name': "TW WhatsApp Integration",

    'summary': "WhatsApp Integration Odoo to send blast message's customer",

    'description': """
WhatsApp Integration Odoo to send blast message's customer
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Web / TW Web',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_config_files',
        'tw_api',
        'tw_branch_setting',
        'tw_selection'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_whatsapp_inbox_view.xml',
        'views/tw_whatsapp_outbox_view.xml',
        'views/tw_whatsapp_content_template_view.xml',
        'views/tw_branch_setting_inherit_view.xml',
        'views/tw_api_configuration_inherit_view.xml',
        'views/tw_selection_template_whatsapp_view.xml',
        'views/tw_menu.xml',
        
        'data/scheduled_actions.xml',
        'data/tw_whatsapp_content_template_type.xml',
        'data/tw_whatsapp_content_template_data.xml',
        'data/tw_whatsapp_api_config_data.xml',
    ],

}

