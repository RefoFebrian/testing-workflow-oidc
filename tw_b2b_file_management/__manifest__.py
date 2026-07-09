# -*- coding: utf-8 -*-
{
    'name': "TW B2B File Management",

    'summary': "Management B2B / MFT File",

    'description': """
        Module used to perform B2B File or MFT File Upload function or Monitoring function and etc.
    """,

    'author': "TDM / Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','base_suspend_security','tw_b2b_file','tw_api','tw_file_dropzone_widget'],

    'external_dependencies': {'python' : ['pysftp']},
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/tw_api_configuration_type_data.xml',
        # 'data/tw_b2b_file_extension_data.xml',
        'data/tw_b2b_file_server_configuration_data.xml',

        'views/tw_b2b_file_monitoring_view.xml',
        'views/tw_b2b_file_upload_view.xml',
        'views/tw_b2b_file_upload_wizard_view.xml',
        'views/tw_b2b_file_server_configuration_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}
